"""Caminhos, banco de dados (SQLite), migrações e registro de eventos."""
import os, time, json, sqlite3, collections
from pathlib import Path
from dotenv import load_dotenv

BASE = Path(__file__).resolve().parent          # não depende de onde o servidor foi iniciado
load_dotenv(BASE / ".env")
DATA = Path(os.getenv("HERO_DATA_DIR", BASE))
SETTINGS_FILE = DATA / "settings.json"          # legado: migrado para o banco no primeiro cadastro
DB = DATA / "hero.db"
LOGS = collections.deque(maxlen=200)


def log(msg):
    LOGS.appendleft({"t": time.strftime("%H:%M:%S"), "msg": msg})


def q(sql, args=()):
    c = sqlite3.connect(DB)
    c.row_factory = sqlite3.Row
    try:
        c.execute("PRAGMA foreign_keys=ON")
        cur = c.execute(sql, args)
        c.commit()
        return [dict(r) for r in cur.fetchall()], cur.lastrowid
    finally:
        c.close()


def record(uid, kind, meta=None):
    """Registra um evento de uso (só contagens e metadados, nunca o texto das conversas)."""
    q("INSERT INTO events(user_id, ts, kind, meta) VALUES(?,?,?,?)",
      (uid, time.time(), kind, json.dumps(meta or {}, ensure_ascii=False)))


def migrate():
    c = sqlite3.connect(DB)
    try:
        c.execute("CREATE TABLE IF NOT EXISTS conv(id INTEGER PRIMARY KEY AUTOINCREMENT, title TEXT, updated REAL)")
        c.execute("CREATE TABLE IF NOT EXISTS task(id INTEGER PRIMARY KEY AUTOINCREMENT, text TEXT, done INTEGER DEFAULT 0)")
        v = c.execute("PRAGMA user_version").fetchone()[0]
        if v < 1:   # v1: mensagens com chave estrangeira
            old = c.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='msg'").fetchone()
            if old:
                c.execute("ALTER TABLE msg RENAME TO msg_old")
            c.execute("CREATE TABLE msg(id INTEGER PRIMARY KEY AUTOINCREMENT, "
                      "conv INTEGER NOT NULL REFERENCES conv(id) ON DELETE CASCADE, "
                      "role TEXT NOT NULL, content TEXT NOT NULL)")
            if old:
                c.execute("INSERT INTO msg(id, conv, role, content) SELECT id, conv, role, content "
                          "FROM msg_old WHERE conv IN (SELECT id FROM conv)")
                c.execute("DROP TABLE msg_old")
            c.execute("PRAGMA user_version=1")
            c.commit()
        if v < 2:   # v2: contas, sessões, configurações por usuário, eventos e relatórios
            c.executescript("""
            CREATE TABLE IF NOT EXISTS users(id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL UNIQUE COLLATE NOCASE, pw TEXT NOT NULL,
                is_admin INTEGER NOT NULL DEFAULT 0, created REAL NOT NULL);
            CREATE TABLE IF NOT EXISTS sessions(token_hash TEXT PRIMARY KEY,
                user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE, expires REAL NOT NULL);
            CREATE TABLE IF NOT EXISTS settings(user_id INTEGER PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
                data TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS events(id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                ts REAL NOT NULL, kind TEXT NOT NULL, meta TEXT NOT NULL DEFAULT '{}');
            CREATE INDEX IF NOT EXISTS ix_events ON events(user_id, ts);
            CREATE TABLE IF NOT EXISTS reports(user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                month TEXT NOT NULL, data TEXT, analysis TEXT, generated REAL, PRIMARY KEY(user_id, month));
            ALTER TABLE conv ADD COLUMN user_id INTEGER REFERENCES users(id) ON DELETE CASCADE;
            ALTER TABLE conv ADD COLUMN created REAL;
            ALTER TABLE task ADD COLUMN user_id INTEGER REFERENCES users(id) ON DELETE CASCADE;
            ALTER TABLE task ADD COLUMN created REAL;
            ALTER TABLE task ADD COLUMN done_at REAL;
            ALTER TABLE msg ADD COLUMN ts REAL;
            UPDATE conv SET created=updated WHERE created IS NULL;
            UPDATE msg SET ts=(SELECT updated FROM conv WHERE conv.id=msg.conv) WHERE ts IS NULL;
            CREATE INDEX IF NOT EXISTS ix_msg_conv ON msg(conv);
            PRAGMA user_version=2;
            """)
        c.commit()
    finally:
        c.close()


migrate()
