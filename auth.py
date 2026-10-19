"""Contas, senhas (scrypt), sessões por cookie e proteção contra força bruta."""
import os, re, hmac, time, hashlib, secrets, sqlite3
from urllib.parse import urlparse
from fastapi import APIRouter, Depends, HTTPException, Request, Response
from pydantic import BaseModel, Field
import core
from core import q, log

SESSION_DAYS = 30
COOKIE = "hero_session"
router = APIRouter(prefix="/api/auth")
FAILS = {}


def hash_pw(pw, salt=None):
    salt = salt or os.urandom(16)
    h = hashlib.scrypt(pw.encode(), salt=salt, n=2 ** 14, r=8, p=1, dklen=32)
    return f"scrypt${salt.hex()}${h.hex()}"


def check_pw(pw, stored):
    try:
        _, s, h = stored.split("$")
        calc = hashlib.scrypt(pw.encode(), salt=bytes.fromhex(s), n=2 ** 14, r=8, p=1, dklen=32)
        return hmac.compare_digest(calc.hex(), h)
    except Exception:
        return False


DUMMY = hash_pw("senha-falsa-para-igualar-o-tempo")   # evita revelar se o usuário existe pelo tempo de resposta


def _sha(tok):
    return hashlib.sha256(tok.encode()).hexdigest()


def _blocked(*keys):
    now = time.time()
    for k, limit in keys:
        FAILS[k] = [t for t in FAILS.get(k, []) if now - t < 600]
        if len(FAILS[k]) >= limit:
            return True
    return False


def _fail(*keys):
    for k, _ in keys:
        FAILS.setdefault(k, []).append(time.time())


def _start_session(uid, request, response):
    q("DELETE FROM sessions WHERE expires<?", (time.time(),))
    tok = secrets.token_urlsafe(32)
    q("INSERT INTO sessions(token_hash, user_id, expires) VALUES(?,?,?)",
      (_sha(tok), uid, time.time() + SESSION_DAYS * 86400))
    response.set_cookie(COOKIE, tok, max_age=SESSION_DAYS * 86400, httponly=True, samesite="strict",
                        secure=request.url.scheme == "https", path="/")


def current_user(request: Request):
    if request.method not in ("GET", "HEAD", "OPTIONS"):      # defesa extra contra CSRF
        origin = request.headers.get("origin")
        if origin and urlparse(origin).netloc != request.headers.get("host"):
            raise HTTPException(403, "Origem não permitida.")
    tok = request.cookies.get(COOKIE)
    if tok:
        rows = q("SELECT u.id, u.username, u.is_admin FROM sessions s JOIN users u ON u.id=s.user_id "
                 "WHERE s.token_hash=? AND s.expires>?", (_sha(tok), time.time()))[0]
        if rows:
            return rows[0]
    raise HTTPException(401, "Entre para continuar.")


class Cred(BaseModel):
    username: str = Field(min_length=3, max_length=32)
    password: str = Field(min_length=8, max_length=128)


def _signup_open():
    n = q("SELECT COUNT(*) AS n FROM users")[0][0]["n"]
    return n == 0 or os.getenv("ALLOW_SIGNUP") == "1", n


@router.get("/status")
def status():
    open_, n = _signup_open()
    return {"has_users": n > 0, "signup_open": open_}


@router.post("/register")
def register(c: Cred, request: Request, response: Response):
    open_, n = _signup_open()
    if not open_:
        raise HTTPException(403, "O cadastro está fechado. Peça ao administrador para liberar.")
    name = c.username.strip()
    if not re.fullmatch(r"[A-Za-z0-9_.-]{3,32}", name):
        raise HTTPException(422, "Use de 3 a 32 letras, números, ponto, hífen ou sublinhado no usuário.")
    try:
        uid = q("INSERT INTO users(username, pw, is_admin, created) VALUES(?,?,?,?)",
                (name, hash_pw(c.password), 1 if n == 0 else 0, time.time()))[1]
    except sqlite3.IntegrityError:
        raise HTTPException(409, "Esse nome de usuário já existe.")
    if n == 0:   # o primeiro usuário herda os dados criados antes de existir login
        q("UPDATE conv SET user_id=? WHERE user_id IS NULL", (uid,))
        q("UPDATE task SET user_id=? WHERE user_id IS NULL", (uid,))
        if core.SETTINGS_FILE.exists():
            q("INSERT OR REPLACE INTO settings(user_id, data) VALUES(?,?)",
              (uid, core.SETTINGS_FILE.read_text(encoding="utf-8")))
            os.replace(core.SETTINGS_FILE, core.SETTINGS_FILE.with_suffix(".json.bak"))
    log("conta criada")
    _start_session(uid, request, response)
    return {"ok": True}


@router.post("/login")
def login(c: Cred, request: Request, response: Response):
    ip, name = request.client.host if request.client else "?", c.username.strip().lower()
    keys = ((("u", ip, name), 5), (("ip", ip), 20))
    if _blocked(*keys):
        raise HTTPException(429, "Muitas tentativas. Tente de novo em alguns minutos.")
    row = q("SELECT id, pw FROM users WHERE username=?", (name,))[0]
    ok = check_pw(c.password, row[0]["pw"] if row else DUMMY)
    if not (row and ok):
        _fail(*keys)
        log("tentativa de login recusada")
        raise HTTPException(401, "Usuário ou senha incorretos.")
    FAILS.pop(("u", ip, name), None)
    _start_session(row[0]["id"], request, response)
    return {"ok": True}


@router.post("/logout")
def logout(request: Request, response: Response):
    tok = request.cookies.get(COOKIE)
    if tok:
        q("DELETE FROM sessions WHERE token_hash=?", (_sha(tok),))
    response.delete_cookie(COOKIE, path="/")
    return {"ok": True}


@router.get("/me")
def me(u=Depends(current_user)):
    return {"id": u["id"], "username": u["username"], "is_admin": bool(u["is_admin"])}


class PwIn(BaseModel):
    current: str = Field(max_length=128)
    new: str = Field(min_length=8, max_length=128)


@router.post("/password")
def change_password(b: PwIn, request: Request, u=Depends(current_user)):
    key = (("pw", u["id"]), 5)
    if _blocked(key):
        raise HTTPException(429, "Muitas tentativas. Tente de novo em alguns minutos.")
    row = q("SELECT pw FROM users WHERE id=?", (u["id"],))[0][0]
    if not check_pw(b.current, row["pw"]):
        _fail(key)
        raise HTTPException(401, "Senha atual incorreta.")
    q("UPDATE users SET pw=? WHERE id=?", (hash_pw(b.new), u["id"]))
    q("DELETE FROM sessions WHERE user_id=? AND token_hash<>?", (u["id"], _sha(request.cookies.get(COOKIE, ""))))
    log("senha alterada")
    return {"ok": True}
