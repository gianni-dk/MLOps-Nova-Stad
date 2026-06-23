import os
import io
import csv
from datetime import datetime
import mlflow
import mlflow.sklearn
import pandas as pd
import numpy as np
import logging
import torch
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_squared_error
from torchvision.models.detection import (
    ssdlite320_mobilenet_v3_large,
    SSDLite320_MobileNet_V3_Large_Weights
)
from PIL import Image
from fastapi import FastAPI, UploadFile, File
import joblib

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class DataMonitor:
    @staticmethod
    def log_data_shape(step_name, df):
        logger.info(f"[{step_name}] Data dimensies: {df.shape}")

    @staticmethod
    def check_missing_values(df):
        missing = df.isnull().sum().sum()
        if missing > 0:
            logger.warning(f"Let op: {missing} ontbrekende waarden gedetecteerd.")
        else:
            logger.info("Geen ontbrekende waarden gedetecteerd.")

    @staticmethod
    def trigger_alert(df):
        stats = {
            "timestamp": [pd.Timestamp.now().isoformat()],
            "rows": [df.shape[0]],
            "columns": [df.shape[1]],
            "missing_values": [int(df.isnull().sum().sum())],
            "mean_traffic_volume": [
                round(df["traffic_volume"].mean(), 2)
                if "traffic_volume" in df.columns else None
            ]
        }
        stats_df = pd.DataFrame(stats)
        file_exists = os.path.isfile("monitoring_metrics.csv")
        stats_df.to_csv(
            "monitoring_metrics.csv", mode="a", header=not file_exists, index=False
        )
        logger.info("Statistieken opgeslagen in monitoring_metrics.csv")


class DataIngestor:
    def __init__(self, url):
        self.url = url

    def load_data(self):
        chunks = pd.read_csv(self.url, chunksize=10000)
        df = pd.concat(chunks, ignore_index=True)
        DataMonitor.log_data_shape("Data Ingestion", df)
        DataMonitor.trigger_alert(df)
        return df


class Preprocessor:
    def process(self, df):
        DataMonitor.check_missing_values(df)
        df["date_time"] = pd.to_datetime(df["date_time"])
        df["hour"] = df["date_time"].dt.hour
        X = df[["hour"]]
        y = df["traffic_volume"]
        return train_test_split(X, y, test_size=0.2, shuffle=False)


class CloudModel:
    def __init__(self):
        self.model_path = "cloud_model.pkl"
        self.model = RandomForestRegressor(random_state=42, n_estimators=50)
        self.is_trained = False

        if os.path.exists(self.model_path):
            self.model = joblib.load(self.model_path)
            self.is_trained = True
            logger.info("Bestaand model geladen vanaf schijf.")

    def train(self, X_train, y_train):
        if not self.is_trained:
            logger.info("Nieuw model wordt getraind...")
            mlflow.set_experiment("nova_stad_traffic_prediction")
            with mlflow.start_run():
                mlflow.log_param("n_estimators", self.model.n_estimators)
                mlflow.log_param("random_state", self.model.random_state)
                self.model.fit(X_train, y_train)
                train_rmse = float(
                    np.sqrt(
                        mean_squared_error(y_train, self.model.predict(X_train))
                    )
                )
                mlflow.log_metric("train_rmse", round(train_rmse, 2))
                mlflow.sklearn.log_model(self.model, "random_forest_model")
            joblib.dump(self.model, self.model_path)
            self.is_trained = True
            logger.info(f"Model succesvol opgeslagen als {self.model_path}")

    def predict(self, hour):
        if not self.is_trained:
            raise ValueError("Model is niet getraind.")
        return float(self.model.predict([[hour]])[0])


class EdgeModel:
    def __init__(self):
        self.weights = SSDLite320_MobileNet_V3_Large_Weights.DEFAULT
        self.model = ssdlite320_mobilenet_v3_large(weights=self.weights)
        self.model.eval()
        self.preprocess = self.weights.transforms()
        self.categories = self.weights.meta["categories"]

    def predict(self, image_bytes):
        image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
        batch = [self.preprocess(image)]
        with torch.no_grad():
            prediction = self.model(batch)[0]
        results = []
        for i, score in enumerate(prediction["scores"]):
            if score > 0.5:
                label_idx = prediction["labels"][i].item()
                label_name = self.categories[label_idx]
                # Bounding box coördinaten [x_min, y_min, x_max, y_max]
                box = prediction["boxes"][i].tolist()
                if label_name in ['car', 'person', 'bus', 'truck', 'bicycle', 'motorcycle']:
                    results.append({
                        "object": label_name,
                        "score": round(score.item(), 2),
                        "box": [round(b, 2) for b in box]
                    })
        return {"detections": results, "count": len(results)}


DATA_URL = (
    "https://archive.ics.uci.edu/ml/machine-learning-databases/"
    "00492/Metro_Interstate_Traffic_Volume.csv.gz"
)

ingestor = DataIngestor(DATA_URL)
preprocessor = Preprocessor()
cloud_model = CloudModel()
edge_model = EdgeModel()

if not getattr(cloud_model, "is_trained", False):
    logger.info("Geen bestaand model gevonden. Koude start: data inladen en trainen...")
    raw_data = ingestor.load_data()
    X_train, X_test, y_train, y_test = preprocessor.process(raw_data)
    cloud_model.train(X_train, y_train)

app = FastAPI(
    title="Nova Stad MLOps API",
    description="API voor Edge en Cloud modellen."
)


@app.get("/health")
def health_check():
    return {
        "status": "online",
        "cloud_model_trained": getattr(cloud_model, "is_trained", False)
    }


@app.get("/cloud/predict_traffic")
def predict_traffic(hour: int):
    if hour < 0 or hour > 23:
        return {"error": "Uur moet tussen 0 en 23 liggen."}
    try:
        prediction = cloud_model.predict(hour)
        logger.info(f"Cloud API request voor uur {hour}: voorspelling {prediction:.2f}")
        file_exists = os.path.isfile("api_live_logs.csv")
        with open("api_live_logs.csv", mode="a", newline="") as file:
            writer = csv.writer(file)
            if not file_exists:
                writer.writerow(["timestamp", "hour", "predicted_traffic_volume"])
            writer.writerow([datetime.now().isoformat(), hour, round(prediction, 2)])
        return {"hour": hour, "predicted_traffic_volume": prediction}
    except Exception as e:
        logger.error(f"Fout in Cloud API: {e}")
        return {"error": str(e)}


@app.post("/edge/detect_objects")
def detect_objects(file: UploadFile = File(...)):
    try:
        contents = file.file.read()
        results = edge_model.predict(contents)
        return {"filename": file.filename, "results": results}
    except Exception as e:
        logger.error(f"Fout in Edge API: {e}")
        return {"error": str(e)}
