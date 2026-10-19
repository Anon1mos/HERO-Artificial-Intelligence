"""Relatório mensal: agrega o uso da HERO (sem enviar o texto das conversas a nenhum provedor)."""
import re, json, time, datetime as dt
from collections import Counter
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import HTMLResponse
import core
from core import q
from auth import current_user
from ai import ask_ai, explain

router = APIRouter(prefix="/api/reports")
MESES = ["janeiro", "fevereiro", "março", "abril", "maio", "junho", "julho", "agosto", "setembro", "outubro", "novembro", "dezembro"]
DIAS = ["segunda", "terça", "quarta", "quinta", "sexta", "sábado", "domingo"]
STOP = set("""para com uma que não nao mais como mas foi são sao por seu sua seus suas dos das nos nas ele ela eles elas isso isto
esse essa esses essas aqui ali tem ter está estão estou tudo todo toda todos todas muito muita quando onde qual quais porque pois
então entao ainda também tambem só sobre entre depois antes até ate cada outro outra outros outras mesmo mesma seja sendo vai vou
vamos pode posso quero queria gostaria preciso fazer favor obrigado obrigada olá ola oi bom boa dia tarde noite hero você voce meu
minha meus minhas dele dela deles delas desse dessa desses dessas deste desta neste nesta nesse nessa algo alguma algum pouco
coisa coisas fazem fazer faça faca explique explica me ajude ajuda""".split())
ACT_KINDS = ("briefing", "command", "voice")
MONTH_RE = re.compile(r"^\d{4}-(0[1-9]|1[0-2])$")


def _d(ts):
    return dt.datetime.fromtimestamp(ts)


def month_range(month):
    y, m = map(int, month.split("-"))
    return dt.datetime(y, m, 1), dt.datetime(y + (m == 12), m % 12 + 1, 1)


def label(month):
    y, m = map(int, month.split("-"))
    return f"{MESES[m - 1]} de {y}"


def prev_month(month):
    y, m = map(int, month.split("-"))
    return f"{y - (m == 1)}-{(m - 2) % 12 + 1:02d}"


def basic(uid, t0, t1):
    um = q("SELECT m.ts FROM msg m JOIN conv c ON c.id=m.conv WHERE c.user_id=? AND m.role='user' AND m.ts>=? AND m.ts<?", (uid, t0, t1))[0]
    ev = q("SELECT ts, kind FROM events WHERE user_id=? AND ts>=? AND ts<?", (uid, t0, t1))[0]
    done = q("SELECT done_at FROM task WHERE user_id=? AND done=1 AND done_at>=? AND done_at<?", (uid, t0, t1))[0]
    made = q("SELECT created FROM task WHERE user_id=? AND created>=? AND created<?", (uid, t0, t1))[0]
    days = ({_d(r["ts"]).date() for r in um} | {_d(r["ts"]).date() for r in ev}
            | {_d(r["done_at"]).date() for r in done} | {_d(r["created"]).date() for r in made})
    return {"messages": len(um), "active_days": len(days), "tasks_completed": len(done),
            "briefings": sum(1 for e in ev if e["kind"] == "briefing")}, days


def _pct(a, b):
    return None if not b else round((a - b) / b * 100)


def build_report(uid, month):
    start, end = month_range(month)
    t0, t1, ndays = start.timestamp(), end.timestamp(), (end - start).days
    now = time.time()
    partial = t0 <= now < t1
    base, days = basic(uid, t0, t1)
    prev, _ = basic(uid, *(x.timestamp() for x in month_range(prev_month(month))))

    msgs = q("SELECT m.role, m.content, m.ts, m.conv, c.title FROM msg m JOIN conv c ON c.id=m.conv "
             "WHERE c.user_id=? AND m.ts>=? AND m.ts<? ORDER BY m.ts", (uid, t0, t1))[0]
    ev = q("SELECT ts, kind, meta FROM events WHERE user_id=? AND ts>=? AND ts<? ORDER BY ts", (uid, t0, t1))[0]
    made = q("SELECT text, created, done, done_at FROM task WHERE user_id=? AND created>=? AND created<?", (uid, t0, t1))[0]
    done = q("SELECT text, created, done_at FROM task WHERE user_id=? AND done=1 AND done_at>=? AND done_at<? ORDER BY done_at", (uid, t0, t1))[0]
    pending = q("SELECT text, created FROM task WHERE user_id=? AND done=0 AND (created IS NULL OR created<?) ORDER BY id", (uid, t1))[0]

    user_msgs = [m for m in msgs if m["role"] == "user"]
    bot_msgs = [m for m in msgs if m["role"] != "user"]
    acts = ([m["ts"] for m in user_msgs] + [e["ts"] for e in ev if e["kind"] in ACT_KINDS]
            + [t["created"] for t in made] + [t["done_at"] for t in done])
    daily, hours, wd = [0] * ndays, [0] * 24, [0] * 7
    for ts in acts:
        d = _d(ts)
        daily[d.day - 1] += 1
        hours[d.hour] += 1
        wd[d.weekday()] += 1

    words = Counter()
    for m in user_msgs:
        for w in re.findall(r"[a-záàâãéêíóôõúç]{4,}", m["content"].lower()):
            if w not in STOP:
                words[w] += 1
    wc = lambda L: sum(len(m["content"].split()) for m in L)
    per_conv = Counter(m["conv"] for m in msgs)
    titles = {m["conv"]: m["title"] for m in msgs}

    meta = lambda e: json.loads(e["meta"] or "{}")
    briefs = [(e, meta(e)) for e in ev if e["kind"] == "briefing"]
    weather = {}
    for e, m in briefs:
        if "tmin" in m:
            weather[_d(e["ts"]).date().isoformat()] = {"day": _d(e["ts"]).date().isoformat(), "tmin": m["tmin"], "tmax": m["tmax"], "rain": m.get("rain", 0)}
    wlist = [weather[k] for k in sorted(weather)]
    news = Counter()
    for _, m in briefs:
        news.update(m.get("news", {}))
    hands = [meta(e) for e in ev if e["kind"] == "hands"]
    cmds = Counter(meta(e).get("name") or "Outros" for e in ev if e["kind"] == "command")

    hrs = [(t["done_at"] - t["created"]) / 3600 for t in done if t["created"]]
    streak = best = 0
    for i in range(1, ndays + 1):
        streak = streak + 1 if dt.date(start.year, start.month, i) in days else 0
        best = max(best, streak)

    hl = []
    if max(daily, default=0):
        i = daily.index(max(daily))
        hl.append(f"Dia mais ativo: {i + 1:02d}/{start.month:02d}, com {daily[i]} interações.")
        hl.append(f"Horário de pico: {hours.index(max(hours)):02d}h. Dia da semana mais ativo: {DIAS[wd.index(max(wd))]}.")
    if best > 1:
        hl.append(f"Maior sequência de dias ativos: {best} dias seguidos.")
    if prev["messages"]:
        dlt = base["messages"] - prev["messages"]
        hl.append(f"Mensagens enviadas: {dlt:+d} ({_pct(base['messages'], prev['messages']):+d}%) em relação a {label(prev_month(month))}.")
    if hrs:
        hl.append(f"Tempo médio para concluir uma tarefa: {sum(hrs) / len(hrs):.1f} h.")
    if wlist:
        rainy = sum(1 for w in wlist if w["rain"] >= 50)
        hl.append(f"Clima nos dias com briefing: máxima média de {sum(w['tmax'] for w in wlist) / len(wlist):.0f}°C e {rainy} dia(s) com chuva provável.")
    if per_conv:
        cid, n = per_conv.most_common(1)[0]
        hl.append(f"Conversa mais longa: “{titles[cid]}”, com {n} mensagens.")

    return {
        "month": month, "label": label(month), "days": ndays, "partial": partial, "generated": now,
        "summary": {**base, "conversations": len(per_conv), "bot_messages": len(bot_msgs),
                    "avg_words_user": round(wc(user_msgs) / len(user_msgs), 1) if user_msgs else 0,
                    "avg_words_bot": round(wc(bot_msgs) / len(bot_msgs), 1) if bot_msgs else 0},
        "previous": {**prev, "label": label(prev_month(month))},
        "highlights": hl, "daily": daily, "hours": hours, "weekday": wd, "weekday_names": DIAS,
        "topics": words.most_common(12),
        "top_convs": [{"title": titles[c], "count": n} for c, n in per_conv.most_common(5)],
        "tasks": {"created": len(made), "completed": len(done), "pending": len(pending),
                  "rate": round(len([t for t in made if t["done"]]) / len(made) * 100) if made else None,
                  "avg_hours": round(sum(hrs) / len(hrs), 1) if hrs else None,
                  "completed_list": [t["text"] for t in done][:25], "pending_list": [t["text"] for t in pending][:25]},
        "briefings": {"count": len(briefs), "days": len({_d(e["ts"]).date() for e, _ in briefs}),
                      "tmin_avg": round(sum(w["tmin"] for w in wlist) / len(wlist), 1) if wlist else None,
                      "tmax_avg": round(sum(w["tmax"] for w in wlist) / len(wlist), 1) if wlist else None,
                      "rainy_days": sum(1 for w in wlist if w["rain"] >= 50), "weather": wlist,
                      "emails": {k: sum(m.get(k, 0) for _, m in briefs) for k in ("att", "info", "noise")},
                      "news": dict(news.most_common()), "agenda_events": sum(m.get("agenda") or 0 for _, m in briefs)},
        "usage": {"voice": sum(1 for e in ev if e["kind"] == "voice"), "commands": cmds.most_common(10),
                  "hands": {"sessions": len(hands), **{k: sum(h.get(k, 0) for h in hands) for k in ("seconds", "clicks", "swipes", "zooms", "drags", "scrolls")}}},
    }


def load_report(uid, month, refresh=False):
    if not MONTH_RE.match(month):
        raise HTTPException(422, "Mês inválido. Use o formato AAAA-MM.")
    cur = dt.date.today().strftime("%Y-%m")
    if month > cur:
        raise HTTPException(422, "Esse mês ainda não começou.")
    row = (q("SELECT data, analysis FROM reports WHERE user_id=? AND month=?", (uid, month))[0] or [None])[0]
    if month < cur and row and row["data"] and not refresh:      # mês fechado fica congelado
        data = json.loads(row["data"])
    else:
        data = build_report(uid, month)
        q("INSERT INTO reports(user_id, month, data, generated) VALUES(?,?,?,?) "
          "ON CONFLICT(user_id, month) DO UPDATE SET data=excluded.data, generated=excluded.generated",
          (uid, month, json.dumps(data, ensure_ascii=False), time.time()))
    data["analysis"] = row["analysis"] if row else None
    return data


@router.get("")
def months(u=Depends(current_user)):
    uid = u["id"]
    firsts = [r["t"] for r in (
        q("SELECT MIN(m.ts) AS t FROM msg m JOIN conv c ON c.id=m.conv WHERE c.user_id=?", (uid,))[0]
        + q("SELECT MIN(ts) AS t FROM events WHERE user_id=?", (uid,))[0]
        + q("SELECT MIN(created) AS t FROM task WHERE user_id=?", (uid,))[0]) if r["t"]]
    today = dt.date.today()
    y, m = (_d(min(firsts)).year, _d(min(firsts)).month) if firsts else (today.year, today.month)
    out = []
    while (y, m) <= (today.year, today.month):
        out.append(f"{y}-{m:02d}")
        y, m = y + (m == 12), m % 12 + 1
    return {"months": out[::-1], "current": today.strftime("%Y-%m")}


@router.get("/{month}")
def get_report(month: str, refresh: bool = False, u=Depends(current_user)):
    return load_report(u["id"], month, refresh)


@router.post("/{month}/analysis")
async def analysis(month: str, u=Depends(current_user)):
    d = load_report(u["id"], month)
    stats = {k: d[k] for k in ("summary", "previous", "weekday", "weekday_names")}
    stats["peak_hour"] = d["hours"].index(max(d["hours"])) if any(d["hours"]) else None
    stats["tasks"] = {k: v for k, v in d["tasks"].items() if not k.endswith("_list")}
    stats["briefings"] = {k: v for k, v in d["briefings"].items() if k != "weather"}
    stats["usage"] = d["usage"]
    prompt = (f"Escreva uma análise do meu uso do assistente em {d['label']}{' (mês em andamento)' if d['partial'] else ''}. "
              "Use SOMENTE os números abaixo, sem inventar nada. Estrutura: 3 pontos fortes, 2 pontos de atenção e 2 sugestões práticas, "
              "em português, em tópicos curtos, no máximo 10 linhas.\n" + json.dumps(stats, ensure_ascii=False))
    try:
        text = await ask_ai([{"role": "user", "content": prompt}])
    except Exception as e:
        raise HTTPException(502, explain(e))
    q("UPDATE reports SET analysis=? WHERE user_id=? AND month=?", (text, u["id"], month))
    return {"analysis": text}


PAGE = """<!doctype html><html lang="pt-BR"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>HERO — Relatório de __LABEL__</title>
<style>:root{--text:#16202e;--panel:#fff;--panel2:#f2f5fa;--line:#d3dbe8;--accent:#0b63e5;--dim:#58687e}
body{margin:0;background:#eef2f8;color:var(--text);font:15px/1.5 "Segoe UI",system-ui,sans-serif}
main{max-width:980px;margin:0 auto;padding:24px 18px 48px}
@media print{body{background:#fff}main{padding:0}.rp-card,.rp-kpi{break-inside:avoid}}</style></head>
<body><main id="r"></main><script>__JS__</script>
<script>renderReport(document.getElementById("r"),__DATA__);if(location.search.includes("print=1"))setTimeout(()=>print(),500);</script></body></html>"""


@router.get("/{month}/export")
def export(month: str, inline: bool = False, u=Depends(current_user)):
    d = load_report(u["id"], month)
    js = (core.BASE / "static" / "report.js").read_text(encoding="utf-8")
    payload = json.dumps(d, ensure_ascii=False).replace("</", "<\\/").replace("\u2028", "\\u2028").replace("\u2029", "\\u2029")
    html = PAGE.replace("__LABEL__", d["label"]).replace("__JS__", js).replace("__DATA__", payload)
    headers = {} if inline else {"Content-Disposition": f'attachment; filename="hero-relatorio-{month}.html"'}
    return HTMLResponse(html, headers=headers)
