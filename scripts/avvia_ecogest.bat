@echo off
setlocal
cd /d "%~dp0.."

set "PORT=5050"
for /f "usebackq tokens=1,* delims==" %%A in (".env") do (
  if /I "%%A"=="PORT" set "PORT=%%B"
)

echo Avvio EcoGest Comune su http://127.0.0.1:%PORT%
start "" cmd /c "timeout /t 2 /nobreak >nul & start http://127.0.0.1:%PORT%/"
python run.py
endlocal
