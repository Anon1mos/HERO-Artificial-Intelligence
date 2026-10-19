"""Inicia a HERO sem .bat e sem uvicorn.exe.

Como usar:
  - No VS Code: abra este arquivo e clique no botão de executar (triângulo), ou
  - No terminal da pasta:  .venv\\Scripts\\python.exe iniciar.py
Para parar: Ctrl+C.
"""
import os, sys, threading, time, webbrowser
from pathlib import Path

AQUI = Path(__file__).resolve().parent
os.chdir(AQUI)
sys.path.insert(0, str(AQUI))
PORTA = int(os.getenv("HERO_PORT", "8900"))


def abrir_navegador():
    time.sleep(1.5)
    webbrowser.open(f"http://localhost:{PORTA}")


if __name__ == "__main__":
    import uvicorn
    from server import app
    threading.Thread(target=abrir_navegador, daemon=True).start()
    print(f"HERO em http://localhost:{PORTA}  (Ctrl+C para parar)")
    uvicorn.run(app, host="127.0.0.1", port=PORTA)
