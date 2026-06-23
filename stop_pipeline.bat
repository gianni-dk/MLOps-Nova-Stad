@echo off
echo Afsluiten van de Nova Stad MLOps systemen...
echo.

echo FastAPI (Poort 8000) afsluiten...
FOR /F "tokens=5" %%a IN ('netstat -aon ^| find ":8000" ^| find "LISTENING"') DO taskkill /F /PID %%a > NUL 2>&1

echo Streamlit (Poort 8501) afsluiten...
FOR /F "tokens=5" %%a IN ('netstat -aon ^| find ":8501" ^| find "LISTENING"') DO taskkill /F /PID %%a > NUL 2>&1

echo Ngrok tunnel afsluiten...
taskkill /F /IM ngrok.exe > NUL 2>&1

echo.
echo Alle systemen zijn succesvol afgesloten! 
echo De zwarte schermen verdwijnen nu vanzelf.
timeout /t 3 > NUL