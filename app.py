import os
import sqlite3
import threading
import time
from datetime import datetime, timezone

import requests
from flask import Flask, jsonify, request, render_template_string

APP_NAME = "VIP NUMBER LAB PRO"
DB_PATH = os.environ.get("DB_PATH", "number_lab.db")
BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "").strip()
BOT_ENABLED = bool(BOT_TOKEN)

app = Flask(__name__)

HTML = r"""
<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>VIP Number Lab Pro</title>
<style>
:root{color-scheme:dark;--bg:#090d18;--panel:#141c2d;--line:#2d3a52;--gold:#e8c45b;--muted:#9eacc2}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:#f7f8fb;font:16px system-ui,Arial;padding:18px}
main{max-width:850px;margin:auto}h1{color:var(--gold);margin-bottom:4px}.muted{color:var(--muted);font-size:13px}
.panel{background:var(--panel);border:1px solid var(--line);border-radius:16px;padding:17px;margin:15px 0}
.grid{display:grid;grid-template-columns:repeat(5,minmax(0,1fr));gap:8px}
.tile{background:#202b40;padding:10px 4px;border-radius:10px;text-align:center}
.tile b{display:block;font-size:22px}.tile small{color:var(--muted)}
input,select,button{font:inherit;border-radius:9px;padding:12px}
input,select{width:100%;margin:6px 0 12px;background:#0a1020;color:white;border:1px solid #48566e}
button{border:0;background:var(--gold);color:#151515;font-weight:750;cursor:pointer}
.secondary{background:#354258;color:white}.row{display:grid;grid-template-columns:1fr 1fr;gap:10px}
.cards{display:grid;grid-template-columns:repeat(3,1fr);gap:8px}
.card{background:#202b40;border-radius:12px;padding:12px}.big{font-size:26px;color:var(--gold);font-weight:800}
li{margin:7px 0;overflow-wrap:anywhere}
@media(max-width:480px){body{padding:11px}.grid{gap:5px}.tile{padding:8px 2px}.tile b{font-size:19px}.row{grid-template-columns:1fr}}
</style>
</head>
<body><main>
<h1>✦ VIP NUMBER LAB PRO</h1>
<p class="muted">Historical analytics · manual result entry · no live game connection</p>
<div class="panel">
<h3>Add completed result</h3>
<p class="muted">Only enter results after the round ends. Period ID should be unique.</p>
<label>Period ID</label><input id="period" placeholder="e.g. 2026102311009">
<label>Actual number (0–9)</label><select id="number"><option value="">Choose number</option></select>
<button onclick="addResult()">Save result</button>
<p id="msg" class="muted"></p>
</div>
<div class="panel">
<h3>Historical frequency</h3><div id="freq" class="grid"></div>
<p id="total" class="muted">0 results recorded</p>
</div>
<div class="panel">
<h3>3-Level analysis (historical candidates)</h3>
<p class="muted">Each level shows one distinct number ranked by prior frequency, plus its Big/Small label. These are historical candidates, not reliable future predictions.</p>
<div class="cards">
<div class="card"><small>Level 1 · top frequency</small><div class="big" id="l1num">—</div><small id="l1bs">Waiting for data</small></div>
<div class="card"><small>Level 2 · next candidate</small><div class="big" id="l2num">—</div><small id="l2bs">Waiting for data</small></div>
<div class="card"><small>Level 3 · next candidate</small><div class="big" id="l3num">—</div><small id="l3bs">Waiting for data</small></div>
</div>
<p id="levelNote" class="muted" style="margin-top:12px">Add completed results to calculate historical candidates.</p>
</div>
<div class="panel">
<h3>Walk-forward test (three candidates)</h3>
<p class="muted">For each test round, candidates are chosen only from earlier results. This is a historical test, not a future prediction.</p>
<div class="cards">
<div class="card"><small>Top 1 hit rate</small><div class="big" id="h1">—</div><small id="h1n"></small></div>
<div class="card"><small>Top 2 hit rate</small><div class="big" id="h2">—</div><small id="h2n"></small></div>
<div class="card"><small>Top 3 hit rate</small><div class="big" id="h3">—</div><small id="h3n"></small></div>
</div><div id="backtest" class="muted" style="margin-top:12px"></div>
</div>
<div class="panel">
<h3>Recent history</h3><ol id="history"></ol>
<button class="secondary" onclick="exportCsv()">Export CSV</button>
</div>
<div class="panel">
<h3>Telegram bot</h3>
<p id="botStatus" class="muted">Checking status…</p>
<p class="muted">After deployment, create a bot with @BotFather and set TELEGRAM_BOT_TOKEN in your host's environment variables. Never paste the token into this page or public code.</p>
</div>
<p class="muted">Important: historical frequency cannot reveal hidden server outcomes. No guaranteed win, betting advice, or real-time 91 Club integration is provided.</p>
</main>
<script>
for(let n=0;n<=9;n++) document.getElementById('number').add(new Option(String(n),String(n)));
async function api(path,opts={}){const r=await fetch(path,{headers:{'Content-Type':'application/json'},...opts});const j=await r.json();if(!r.ok)throw new Error(j.error||'Request failed');return j}
async function addResult(){
 const period=document.getElementById('period').value.trim(), number=document.getElementById('number').value;
 if(!period||number===''){document.getElementById('msg').textContent='Period ID aur number dono bharna zaroori hai.';return}
 try{await api('/api/results',{method:'POST',body:JSON.stringify({period_id:period,number:Number(number)})});document.getElementById('period').value='';document.getElementById('number').value='';document.getElementById('msg').textContent='Result saved.';await refresh()}
 catch(e){document.getElementById('msg').textContent=e.message}
}
async function refresh(){
 const d=await api('/api/dashboard');
 document.getElementById('freq').innerHTML=d.frequency.map(x=>`<div class="tile"><b>${x.number}</b><small>${x.count} times</small><br><small>${x.percent}%</small></div>`).join('');
 document.getElementById('total').textContent=`${d.total} results recorded`;
 const levels=d.levels||[];
 for(let k=1;k<=3;k++){
   const item=levels[k-1];
   document.getElementById('l'+k+'num').textContent=item?String(item.number):'—';
   document.getElementById('l'+k+'bs').textContent=item?(item.big_small+' · '+item.count+' historical hit(s)'):'Waiting for data';
 }
 document.getElementById('levelNote').textContent=d.total?`Based on ${d.total} saved result(s). Frequency ranking only; it does not improve or guarantee the next result.`:'Add completed results to calculate historical candidates.';
 for(let k=1;k<=3;k++){document.getElementById('h'+k).textContent=d.backtest.total?d.backtest['top'+k+'_pct']+'%':'—';document.getElementById('h'+k+'n').textContent=d.backtest.total?`${d.backtest['top'+k+'_hits']}/${d.backtest.total} rounds`:''}
 document.getElementById('backtest').textContent=d.backtest.total?`Test rounds: ${d.backtest.total}. Small samples can be misleading; compare against a suitable random baseline.`:'Add at least 6 completed results to begin the walk-forward test.';
 document.getElementById('history').innerHTML=d.recent.length?d.recent.map(x=>`<li>${esc(x.period_id)} — <b>${x.number}</b> (${x.number>=5?'Big':'Small'}) <small>${esc(x.created_at)}</small></li>`).join(''):'<li>No results yet.</li>';
 document.getElementById('botStatus').textContent=d.bot_enabled?'Bot token is configured. Check deployment logs if the bot is not responding.':'Bot token not configured yet.';
}
function esc(s){return String(s).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]))}
async function exportCsv(){const d=await api('/api/results');const lines=['period_id,number,big_small,created_at',...d.results.map(x=>`${JSON.stringify(x.period_id)},${x.number},${x.number>=5?'Big':'Small'},${JSON.stringify(x.created_at)}`)];const a=document.createElement('a');a.href=URL.createObjectURL(new Blob([lines.join('\\n')],{type:'text/csv'}));a.download='vip-number-history.csv';a.click();URL.revokeObjectURL(a.href)}
refresh().catch(e=>document.getElementById('msg').textContent=e.message);
</script></body></html>
"""

def connect():
    con = sqlite3.connect(DB_PATH, timeout=15)
    con.row_factory = sqlite3.Row
    return con

def init_db():
    with connect() as con:
        con.execute("""CREATE TABLE IF NOT EXISTS results(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            period_id TEXT UNIQUE NOT NULL,
            number INTEGER NOT NULL CHECK(number BETWEEN 0 AND 9),
            created_at TEXT NOT NULL
        )""")
init_db()

def get_results():
    with connect() as con:
        rows = con.execute("SELECT period_id, number, created_at FROM results ORDER BY id ASC").fetchall()
    return [dict(r) for r in rows]

def candidate_numbers(previous):
    counts = [previous.count(n) for n in range(10)]
    return sorted(range(10), key=lambda n: (-counts[n], n))[:3]

def build_dashboard():
    results = get_results()
    counts = [sum(1 for r in results if r["number"] == n) for n in range(10)]
    total = len(results)
    freq = [{"number": n, "count": counts[n], "percent": round(counts[n] / total * 100, 1) if total else 0.0} for n in range(10)]
    numbers = [r["number"] for r in results]
    hits = [0, 0, 0]
    tested = 0
    # At least 5 earlier observations are used to select candidates.
    for i in range(5, len(numbers)):
        picks = candidate_numbers(numbers[:i])
        actual = numbers[i]
        tested += 1
        for k in range(3):
            if actual in picks[:k+1]:
                hits[k] += 1
    bt = {"total": tested}
    for k in range(3):
        bt[f"top{k+1}_hits"] = hits[k]
        bt[f"top{k+1}_pct"] = round(hits[k] / tested * 100, 1) if tested else 0
    ranked = sorted(range(10), key=lambda n: (-counts[n], n))
    levels = []
    if total:
        for n in ranked[:3]:
            levels.append({"number": n, "count": counts[n], "big_small": "Big" if n >= 5 else "Small"})
    return {"total": total, "frequency": freq, "recent": list(reversed(results[-30:])), "backtest": bt, "bot_enabled": BOT_ENABLED, "levels": levels}

@app.get("/")
def home():
    return render_template_string(HTML)

@app.get("/health")
def health():
    return jsonify({"ok": True, "service": APP_NAME})

@app.get("/api/dashboard")
def dashboard():
    return jsonify(build_dashboard())

@app.get("/api/results")
def results_endpoint():
    return jsonify({"results": get_results()})

@app.post("/api/results")
def add_result():
    payload = request.get_json(silent=True) or {}
    period = str(payload.get("period_id", "")).strip()
    number = payload.get("number")
    if not period or len(period) > 100:
        return jsonify({"error": "Valid period_id required (1–100 characters)."}), 400
    if isinstance(number, bool) or not isinstance(number, int) or number < 0 or number > 9:
        return jsonify({"error": "number must be an integer from 0 to 9."}), 400
    now = datetime.now(timezone.utc).isoformat(timespec="seconds")
    try:
        with connect() as con:
            con.execute("INSERT INTO results(period_id, number, created_at) VALUES(?,?,?)", (period, number, now))
    except sqlite3.IntegrityError:
        return jsonify({"error": "This period ID already exists. Use a unique period ID."}), 409
    return jsonify({"ok": True})

def telegram_send(chat_id, text):
    if not BOT_TOKEN:
        return
    try:
        requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
                      json={"chat_id": chat_id, "text": text}, timeout=15)
    except requests.RequestException:
        pass

def telegram_poll():
    if not BOT_TOKEN:
        print("Telegram bot disabled: TELEGRAM_BOT_TOKEN not configured.")
        return
    offset = None
    print("Telegram polling bot started.")
    while True:
        try:
            params = {"timeout": 25}
            if offset is not None:
                params["offset"] = offset
            resp = requests.get(f"https://api.telegram.org/bot{BOT_TOKEN}/getUpdates", params=params, timeout=35)
            data = resp.json()
            if not data.get("ok"):
                time.sleep(5)
                continue
            for update in data.get("result", []):
                offset = update["update_id"] + 1
                msg = update.get("message") or update.get("edited_message")
                if not msg or not msg.get("text") or not msg.get("chat"):
                    continue
                chat_id = msg["chat"]["id"]
                text = msg["text"].strip()
                if text.startswith("/start") or text.startswith("/help"):
                    telegram_send(chat_id, "VIP NUMBER LAB PRO\\nCommands:\\n/stats - historical frequency and walk-forward test\\n/add PERIOD NUMBER - save a completed result, e.g. /add 11009 7\\n/recent - latest saved results\\n\\nThis bot analyzes manually entered history; it cannot reveal hidden results or guarantee wins.")
                elif text.startswith("/stats"):
                    d = build_dashboard()
                    top = sorted(d["frequency"], key=lambda x: (-x["count"], x["number"]))[:3]
                    top_text = ", ".join(f'{x["number"]} ({x["count"]})' for x in top) if d["total"] else "No data yet"
                    b = d["backtest"]
                    msg_text = f'Results saved: {d["total"]}\\nMost frequent sample numbers: {top_text}\\nTop-1 walk-forward: {b["top1_pct"]}% ({b["top1_hits"]}/{b["total"]})\\nTop-2 coverage: {b["top2_pct"]}% ({b["top2_hits"]}/{b["total"]})\\nTop-3 coverage: {b["top3_pct"]}% ({b["top3_hits"]}/{b["total"]})\\nHistorical metrics only; not a future prediction.'
                    telegram_send(chat_id, msg_text)
                elif text.startswith("/recent"):
                    recent = list(reversed(get_results()[-10:]))
                    telegram_send(chat_id, "Recent results:\\n" + ("\\n".join(f'{x["period_id"]}: {x["number"]} ({"Big" if x["number"] >= 5 else "Small"})' for x in recent) if recent else "No results yet."))
                elif text.startswith("/add"):
                    parts = text.split()
                    if len(parts) != 3:
                        telegram_send(chat_id, "Usage: /add PERIOD_ID NUMBER\\nExample: /add 11009 7")
                        continue
                    try:
                        period, number = parts[1], int(parts[2])
                        if not 0 <= number <= 9:
                            raise ValueError()
                        with connect() as con:
                            con.execute("INSERT INTO results(period_id, number, created_at) VALUES(?,?,?)",
                                        (period, number, datetime.now(timezone.utc).isoformat(timespec="seconds")))
                        telegram_send(chat_id, f"Saved completed result: {period} = {number} ({'Big' if number >= 5 else 'Small'}).")
                    except ValueError:
                        telegram_send(chat_id, "Number must be 0–9.")
                    except sqlite3.IntegrityError:
                        telegram_send(chat_id, "That period ID already exists.")
                else:
                    telegram_send(chat_id, "Unknown command. Send /help.")
        except Exception as e:
            print("Telegram polling error:", str(e)[:200])
            time.sleep(5)

if BOT_TOKEN:
    threading.Thread(target=telegram_poll, daemon=True).start()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", "5000")))
