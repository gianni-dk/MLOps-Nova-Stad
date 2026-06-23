@echo off
echo Starten van de Nova Stad MLOps Pipeline...
echo.

echo 1. FastAPI Backend starten...
start "NovaStad_Backend" cmd /c "uvicorn app:app --host 0.0.0.0 --port 8000"

echo 2. Wachten tot de API online is...
:check_api
curl -s http://localhost:8000/health > NUL
if %errorlevel% neq 0 (
    timeout /t 1 /nobreak > NUL
    goto check_api
)
echo API is online!

echo 3. Streamlit Dashboard starten...
start "NovaStad_Frontend" cmd /c "streamlit run dashboard.py"

echo 4. Wereldwijde tunnel openen (Ngrok)...
:: VUL HIERONDER JOUW VASTE NGROK DOMEIN IN:
start "NovaStad_Ngrok" cmd /c "ngrok http --url=strut-canon-twerp.ngrok-free.dev 8501"

echo.
echo Het systeem is live! Deel je Ngrok-link met je projectgroep.
echo Je kunt dit zwarte venster sluiten.
exit