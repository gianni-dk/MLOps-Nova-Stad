# Productvereistendocument — Nova Stad MLOps Platform

**Project:** Nova Stad  
**Werkgroep:** Eduard, gianni en Wouter  
**Datum:** 23 Juni 2026


---

## 1. Productoverzicht

Nova Stad is een MLOps-platform dat verkeersstromen in een stedelijke omgeving bewaakt en voorspelt. Het platform bestaat uit twee modellen die samenwerken: een cloudmodel voor verkeersvolume-voorspellingen op basis van historische data, en een edgemodel voor real-time objectdetectie via camerabeelden.

**Doelstellingen:**

- Het cloudmodel voorspelt het verwachte verkeersvolume per uur van de dag, zodat de gemeente vroegtijdig kan bijsturen (bijvoorbeeld met verkeerslichten of omleidingen).
- Het edgemodel detecteert voertuigen en voetgangers in live camerabeelden zonder dat die beelden naar een centrale server hoeven.
- Het platform draait als een API die andere gemeentelijke systemen kunnen aanroepen.
- Alle onderdelen zijn gedocumenteerd, geautomatiseerd en herhaalbaar via een CI/CD-pipeline.

**Belang:**  
Dit systeem levert datagedreven voorspellingen ter ondersteuning van het gemeentelijk verkeersmanagement.

---

## 2. Stakeholders

| Stakeholder | Rol | Belang |
|---|---|---|
| Gemeentelijke IT-afdeling | Eigenaar van de infrastructuur | Wil een stabiel systeem dat weinig handmatig onderhoud vraagt en voldoet aan beveiligingseisen. |
| Verkeerskundigen | Eindgebruiker van de voorspellingen | Willen betrouwbare cijfers over verkeersvolume per tijdstip. Geen technische achtergrond vereist. |
| Burgers | Indirect betrokken | Profiteren van beter verkeersbeheer, maar hebben geen directe toegang tot het systeem. |
| Ontwikkelteam | Bouwers en beheerders | Verantwoordelijk voor het bouwen, testen en overdragen van het platform. |

---

## 3. Datavereisten

**Bron en volume:**  
De trainingsdata is de Metro Interstate Traffic Volume dataset van de UCI Machine Learning Repository. Het bestand wordt via een vaste URL ingeladen door de `DataIngestor`-klasse. Dit automatiseert de data-ingestie. De dataset bevat ruim 48.000 rijen. Voor dit prototype wordt de dataset eenmalig in het geheugen geladen. In productie wordt dit vervangen door een PySpark-gebaseerde streaming data-architectuur op een cloud-cluster (zie ook het notebook, sectie 2.2).

**Kwaliteit:**  
- De `DataMonitor`-klasse controleert bij elke run op ontbrekende waarden en logt een waarschuwing als die worden gevonden.
- De `Preprocessor` verwijdert geen rijen automatisch. Een verkeerskundige of ontwikkelaar moet beslissen hoe ontbrekende waarden worden behandeld.

**Snelheid:**  
- Trainingsdata: batch, geen realtime vereiste.
- Edge-input: afbeeldingen worden per aanvraag aangeleverd via de `/edge/detect_objects` API. De verwerkingstijd per afbeelding moet onder de 2 seconden liggen.

**Privacy en security:**  
- Camerabeelden worden niet opgeslagen. Het edgemodel verwerkt een afbeelding en geeft alleen een lijst van gedetecteerde objecten terug (geen gezichten, geen kentekens).
- De huidige API bevat geen authenticatie. Voor implementatie in een productieomgeving is toevoeging van een API-sleutel of OAuth-laag vereist.
- Verkeersdata bevat geen persoonsgegevens. AVG-risico is laag.

---

## 4. Modelvereisten

### Cloud Model — Verkeersvolume-voorspelling

| Vereiste | Waarde |
|---|---|
| Algoritme | RandomForestRegressor (scikit-learn) |
| Input | Uur van de dag (integer, 0–23) |
| Output | Voorspeld verkeersvolume (float) |
| Prestatie-eis | RMSE onder 1000 voertuigen per uur |
| Trainingstijd | Maximaal 5 minuten op standaard hardware |
| Modelgrootte | Maximaal 50 MB opgeslagen model |
| Endpoint | `GET /cloud/predict_traffic?hour={int}` |
| Herlaadtijd | Model wordt eenmalig getraind en geladen vanaf .pkl bestand |
| Experiment tracking | MLflow — experiment `nova_stad_traffic_prediction` |

### Edge Model — Objectdetectie

| Vereiste | Waarde |
|---|---|
| Architectuur | SSDLite320 MobileNetV3 Large (PyTorch, pre-trained) |
| Input | Afbeelding (JPEG/PNG via HTTP upload) |
| Output | Lijst van gedetecteerde objecten met betrouwbaarheidsscore |
| Drempelwaarde | Alleen objecten met score boven 0.5 worden gerapporteerd |
| Relevante klassen | car, person, bus, truck, bicycle, motorcycle |
| Inferentiesnelheid | Maximaal 2 seconden per afbeelding op CPU |
| Modelgrootte | Pre-trained gewichten, geen extra trainingsdata vereist |
| Endpoint | `POST /edge/detect_objects` (multipart/form-data) |

**Gezamenlijk endpoint:**  
`GET /health` geeft de status van de API en of het cloudmodel is getraind.

### Modelkeuze — Verantwoording

**Cloud Model: RandomForestRegressor**  
De keuze voor RandomForest is gebaseerd op de eigenschappen van de verkeersdata. Het verkeersvolume kent niet-lineaire patronen: ochtend- en avondspits, weekendverschillen en incidentele uitschieters door wegwerkzaamheden of evenementen. RandomForest middelt de uitkomst van meerdere decision trees, waardoor individuele uitschieters minder zwaar wegen. Het model presteert goed op tabular data met dit type niet-lineaire structuur zonder uitgebreide feature engineering. De hyperparameters (`n_estimators=50`, `max_depth=None`) zijn gevalideerd via GridSearchCV (zie notebook, sectie 4.1).

**Edge Model: SSDLite320 MobileNetV3**  
SSDLite320 MobileNetV3 is ontworpen voor CPU-inferentie op hardware met beperkt rekenvermogen. De SSDLite-variant vervangt standaard convoluties door depthwise separable convoluties, wat de rekenbelasting sterk verlaagt ten opzichte van standaard SSD zonder significant precisieverlies voor objectdetectie. De pre-trained COCO-gewichten bevatten alle relevante objectklassen voor dit project (car, bus, truck, bicycle, motorcycle, person). Extra trainingsdata van Nova Stad-camera's is voor het huidige prototype niet vereist. Op standaard CPU-hardware ligt de inferentiesnelheid onder de 2 seconden per afbeelding, in lijn met de gestelde prestatievereiste.

---

## 5. Onderhoud

**CI/CD-pipeline:**  
Het project gebruikt GitHub Actions voor automatische tests. Bij elke push naar de `main`-branch voert de pipeline een syntax-controle (py_compile) uit om te garanderen dat de Python-code foutloos is voordat deze wordt overgedragen. Volledige unit-tests en een Docker-implementatie zijn ontworpen in de theorie, maar vallen buiten de scope van dit prototype.

**Hertrainen (Continuous Training):**  
In de huidige architectuur traint het model eenmalig en slaat het zichzelf op als .pkl bestand. Elk trainingsrun wordt geregistreerd via MLflow: parameters (`n_estimators`, `random_state`), metrics (`train_rmse`) en het modelartefact worden opgeslagen in het MLflow-experiment `nova_stad_traffic_prediction`. Hertraining wordt in de toekomst getriggerd via een geplande cronjob.

**Monitoring:**  
De DataMonitor-klasse schrijft basisstatistieken naar monitoring_metrics.csv bij elke pipeline-run (data monitoring). Daarnaast worden live API-aanvragen voor het cloudmodel weggeschreven naar api_live_logs.csv (inference monitoring). Dit is een lokale simulatie. Voor productie wordt een koppeling met een externe tool (zoals Grafana of Azure Monitor) aanbevolen.

**Bekende beperkingen van de huidige versie:**

- Het cloudmodel gebruikt alleen het uur van de dag als feature. Weersomstandigheden, feestdagen en wegwerkzaamheden worden niet meegenomen.
- De API heeft geen authenticatie.
- Monitoring is lokaal en niet persistent over meerdere servers.
- Het edgemodel gebruikt een generiek pre-trained model. Een model getraind op lokale Nova Stad camerabeelden zou nauwkeuriger zijn.