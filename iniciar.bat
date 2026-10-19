@echo off
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
  echo Nao encontrei a pasta .venv. Veja o README.
  pause
  exit /b 1
)
echo Iniciando a HERO em http://localhost:8900  (feche esta janela para parar)
start "" http://localhost:8900
".venv\Scripts\python.exe" -m uvicorn server:app --host 127.0.0.1 --port 8900
pause
