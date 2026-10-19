"""Provedores de IA (Ollama / Gemini) e tradução de erros em mensagens seguras."""
import os, uuid, logging
from typing import Literal
import httpx
from pydantic import BaseModel, Field
import core  # noqa: F401  (carrega o .env)
from core import log

PROVIDER = os.getenv("PROVIDER", "ollama").lower()
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.2")
GEMINI_KEY = os.getenv("GEMINI_API_KEY", "")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-flash-latest")
SYSTEM = ("Você é a HERO, uma assistente pessoal. Fale sempre no feminino sobre si mesma "
          "(por exemplo: \"estou pronta\", \"obrigada\"). Responda em português do Brasil, "
          "de forma curta, educada e com um leve sarcasmo elegante.")


class AIError(Exception):
    pass


class Msg(BaseModel):
    role: Literal["user", "assistant"]
    content: str = Field(min_length=1, max_length=20000)


class ChatIn(BaseModel):
    messages: list[Msg] = Field(min_length=1, max_length=60)


def model_name():
    return GEMINI_MODEL if PROVIDER == "gemini" else OLLAMA_MODEL


async def ask_ai(messages, system=SYSTEM):
    async with httpx.AsyncClient(timeout=120) as c:
        if PROVIDER == "gemini":
            if not GEMINI_KEY:
                raise AIError("Defina GEMINI_API_KEY no arquivo .env")
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent"
            body = {"systemInstruction": {"parts": [{"text": system}]},
                    "contents": [{"role": "user" if m["role"] == "user" else "model",
                                  "parts": [{"text": m["content"]}]} for m in messages]}
            
            r = await c.post(
                 url,
                json=body,
                headers={"x-goog-api-key": GEMINI_KEY}
            )

            if r.is_error:
                log(f"Gemini HTTP {r.status_code}: {r.text[:1500]}")

            r.raise_for_status()

            try:
                return r.json()["candidates"][0]["content"]["parts"][0]["text"]
            except (KeyError, IndexError, TypeError, ValueError):
                raise AIError("O Gemini devolveu uma resposta vazia ou em formato inesperado.")
        body = {"model": OLLAMA_MODEL, "stream": False,
                "messages": [{"role": "system", "content": system}] + messages}
        r = await c.post(f"{OLLAMA_URL}/api/chat", json=body)
        r.raise_for_status()
        try:
            return r.json()["message"]["content"]
        except (KeyError, TypeError, ValueError):
            raise AIError("O Ollama devolveu uma resposta em formato inesperado.")


def explain(e):
    """Mensagem segura para o usuário; o detalhe técnico fica só no servidor."""
    eid = uuid.uuid4().hex[:8]
    if isinstance(e, AIError):
        msg = str(e)
    elif isinstance(e, httpx.ConnectError):
        msg = "Sem conexão com o Gemini." if PROVIDER == "gemini" else "Não consegui falar com o Ollama. Ele está aberto?"
    elif isinstance(e, httpx.TimeoutException):
        msg = "O modelo demorou demais para responder."
    elif isinstance(e, httpx.HTTPStatusError):
        msg = f"O provedor recusou a requisição (código {e.response.status_code})."
    else:
        logging.exception("erro inesperado %s", eid)
        msg = f"Erro inesperado no modelo (código {eid})."
    log(f"erro {eid}: {type(e).__name__}")
    return msg
