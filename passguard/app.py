import os, io, math, secrets, string, textwrap, datetime
from flask import Flask, render_template, request, jsonify, send_file
from zxcvbn import zxcvbn
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 32 * 1024

LABELS = ["Very weak", "Weak", "Fair", "Strong", "Very strong"]
STEPS = [0, 3, 6, 8, 10]
AMBIGUOUS = set("O0oIl1|")
SYMBOLS = "!@#$%^&*()-_=+[]{};:,.?"
WORDS = """able acid acorn actor agile album alert amber angle apple arch arrow atlas aura autumn bacon badge
baker basil beach beam berry bike birch blade bloom boat bonus brave bread brick bridge brook cabin cactus
camel candle canyon cargo cedar chair chalk charm cherry chess cliff clock cloud clover coast cobalt comet
coral cotton crane creek crown cycle daisy dawn delta desert diner dolphin dragon dream drum eagle earth
echo elbow ember engine fabric falcon fern ferry field flame flint forest fossil fox frost galaxy garden
ginger glacier globe grain grape gravel harbor hazel heron hill honey island ivory jacket jade jungle kettle
kite ladder lake lantern lemon lily lunar maple marble meadow melon mint mirror moon moss mountain nectar
north oasis ocean olive onyx orbit otter paddle panda pearl pepper pillow pine planet plum pond prairie
pulse quartz quiet rabbit radar rain raven reef river robin rocket saddle sage sailor shadow silver sketch
slate solar spark spice spruce stone storm summit sunset tiger timber topaz tower trail tulip valley velvet
violet walnut whale willow winter wizard yellow zebra zephyr""".split()


def lev(a, b):
    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        cur = [i]
        for j, cb in enumerate(b, 1):
            cur.append(min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + (ca != cb)))
        prev = cur
    return prev[-1]


def analyze(pw, personal=(), previous=""):
    pw = pw[:128]
    personal = [str(p).strip()[:60] for p in personal if str(p).strip()][:5]
    previous = (previous or "")[:128]
    z = zxcvbn(pw[:72], user_inputs=personal)
    level, g = z["score"], z["guesses_log10"]
    seq = z["sequence"]
    patterns = any(s["pattern"] in ("spatial", "sequence", "repeat", "date") for s in seq)
    common = any(s["pattern"] == "dictionary" and s.get("dictionary_name") == "passwords"
                 and s.get("rank", 10**6) <= 10000 for s in seq)
    hits = [p for p in personal if len(p) >= 3 and p.lower() in pw.lower()]
    checks = [
        ("At least 12 characters", len(pw) >= 12),
        ("Upper and lowercase letters", any(c.isupper() for c in pw) and any(c.islower() for c in pw)),
        ("Contains a number", any(c.isdigit() for c in pw)),
        ("Contains a symbol", any(not c.isalnum() for c in pw)),
        ("Not a commonly used password", not common),
        ("No keyboard, sequence or repeat patterns", not patterns),
    ]
    if personal:
        checks.append(("Does not contain your personal info", not hits))
    sim = False
    if previous:
        d = lev(pw.lower(), previous.lower())
        sim = d <= 3 or 1 - d / max(len(pw), len(previous), 1) >= 0.7
        checks.append(("Different from your previous password", not sim))
    tips = []
    if z["feedback"]["warning"]:
        tips.append(z["feedback"]["warning"].rstrip(".") + ".")
    tips += z["feedback"]["suggestions"]
    if len(pw) < 12: tips.append("Use at least 12 characters, or try a passphrase.")
    if hits: tips.append("Remove your name, birth year or email from the password.")
    if sim: tips.append("Choose something clearly different from your previous password.")
    if not any(not c.isalnum() for c in pw): tips.append("Add a symbol.")
    pct = min(100, level * 20 + int(min(20, max(0, (g - STEPS[level]) * 5))))
    ct = z["crack_times_display"]
    return {
        "level": level, "label": LABELS[level], "percent": pct,
        "entropy": round(g * 3.3219, 1),
        "crack": [["Online, rate-limited", ct["online_throttling_100_per_hour"]],
                  ["Online, no limit", ct["online_no_throttling_10_per_second"]],
                  ["Offline, slow hash", ct["offline_slow_hashing_1e4_per_second"]],
                  ["Offline, fast hash", ct["offline_fast_hashing_1e10_per_second"]]],
        "checks": [{"text": t, "ok": ok} for t, ok in checks],
        "suggestions": list(dict.fromkeys(tips)),
    }


def gen_random(o):
    pools = []
    if o.get("upper"): pools.append(string.ascii_uppercase)
    if o.get("lower"): pools.append(string.ascii_lowercase)
    if o.get("digits"): pools.append(string.digits)
    if o.get("symbols"): pools.append(SYMBOLS)
    if o.get("noamb"): pools = ["".join(c for c in p if c not in AMBIGUOUS) for p in pools]
    if not pools: return None
    n = max(8, min(64, int(o.get("length", 16))))
    allc = "".join(pools)
    chars = [secrets.choice(p) for p in pools] + [secrets.choice(allc) for _ in range(n - len(pools))]
    secrets.SystemRandom().shuffle(chars)
    return "".join(chars)


def gen_phrase(o):
    n = max(3, min(8, int(o.get("words", 5))))
    sep = o.get("sep") if o.get("sep") in ("-", ".", "_") else "-"
    ws = [secrets.choice(WORDS) for _ in range(n)]
    if o.get("number"): ws.append(str(secrets.randbelow(90) + 10))
    return sep.join(ws)


def make_pdf(length, a):
    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=A4)
    w, h = A4
    st = {"y": h - 60}

    def line(t, size=11, bold=False, dy=18, x=50):
        if st["y"] < 60:
            c.showPage(); st["y"] = h - 60
        c.setFont("Helvetica-Bold" if bold else "Helvetica", size)
        c.drawString(x, st["y"], t); st["y"] -= dy

    line("PassGuard - Password Strength Report", 18, True, 26)
    line(datetime.datetime.now().strftime("Generated %d %B %Y, %H:%M"), 9, dy=26)
    line("The password itself is never included in this report.", 9, dy=26)
    line("Summary", 13, True)
    line(f"Strength: {a['label']} ({a['percent']}/100)")
    line(f"Estimated entropy: {a['entropy']} bits")
    line(f"Length: {length} characters", dy=26)
    line("Estimated time to crack", 13, True)
    for k, v in a["crack"]: line(f"{k}: {v}", x=60)
    st["y"] -= 8
    line("Security checklist", 13, True)
    for ch in a["checks"]: line(f"[{'PASS' if ch['ok'] else 'FAIL'}] {ch['text']}", x=60)
    if a["suggestions"]:
        st["y"] -= 8
        line("Recommendations", 13, True)
        for s in a["suggestions"]:
            for i, part in enumerate(textwrap.wrap(s, 85)):
                line(("- " if i == 0 else "  ") + part, dy=15, x=60)
    c.save(); buf.seek(0)
    return buf


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/check", methods=["POST"])
def api_check():
    d = request.get_json(silent=True) or {}
    pw = d.get("password", "")
    if not isinstance(pw, str) or not pw:
        return jsonify(error="Enter a password."), 400
    try:
        return jsonify(analyze(pw, d.get("personal", []), d.get("previous", "")))
    except Exception:
        return jsonify(error="Analysis failed."), 500


@app.route("/api/generate", methods=["POST"])
def api_generate():
    o = request.get_json(silent=True) or {}
    try:
        pw = gen_phrase(o) if o.get("mode") == "phrase" else gen_random(o)
    except (ValueError, TypeError):
        pw = None
    if not pw:
        return jsonify(error="Select at least one character type."), 400
    return jsonify(password=pw)


@app.route("/api/report", methods=["POST"])
def api_report():
    d = request.get_json(silent=True) or {}
    pw = d.get("password", "")
    if not isinstance(pw, str) or not pw:
        return jsonify(error="Enter a password."), 400
    a = analyze(pw, d.get("personal", []), d.get("previous", ""))
    return send_file(make_pdf(len(pw[:128]), a), mimetype="application/pdf",
                     as_attachment=True, download_name="passguard-report.pdf")


if __name__ == "__main__":
    app.run(host=os.environ.get("HOST", "0.0.0.0"), port=int(os.environ.get("PORT", 5000)))
