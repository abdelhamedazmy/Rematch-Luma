from flask import Flask, request, jsonify, redirect, session, render_template_string, send_file
import json, os, uuid, time, hashlib, csv
from functools import wraps
from datetime import datetime

app = Flask(__name__)
app.secret_key = "SUPER-SECRET-KEY-CHANGE-THIS"

# ================= Files =================
DB_FILE = "keys.json"
USERS_FILE = "users.json"
LOG_FILE = "logs.txt"

# ================= Helpers =================
def log_event(text):
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(f"[{datetime.now()}] {text}\n")

def load_json(file, default):
    if not os.path.exists(file):
        return default
    with open(file, "r", encoding="utf-8") as f:
        return json.load(f)

def save_json(file, data):
    with open(file, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)

def hash_password(p):
    return hashlib.sha256(p.encode()).hexdigest()

# ================= Default Users =================
if not os.path.exists(USERS_FILE):
    save_json(USERS_FILE, {
        "admin": {
            "password": hash_password("123456"),
            "role": "admin",
            "token": str(uuid.uuid4())
        }
    })

# ================= Auth Decorators =================
def login_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if not session.get("user"):
            return redirect("/login")
        return f(*args, **kwargs)
    return wrapper

def admin_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        user = session.get("user")
        users = load_json(USERS_FILE, {})
        if not user or users[user]["role"] != "admin":
            return "Forbidden", 403
        return f(*args, **kwargs)
    return wrapper

# ================= Layout =================
BASE_HTML = """
<!DOCTYPE html>
<html>
<head>
<title>Rematch Egypt Admin</title>
<link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/css/bootstrap.min.css" rel="stylesheet">
<style>
body {
    background: linear-gradient(135deg, #020617, #0b1220);
    color: #e2e8f0;
    font-family: Segoe UI;
}
.navbar {
    background: #020617;
    border-bottom: 1px solid #1f2937;
}
.card {
    background: #0f172a;
    border-radius: 15px;
    border: 1px solid #1f2937;
}
</style>
</head>
<body>
<nav class="navbar px-4 py-3">
  <span class="navbar-brand">🎮 Rematch Egypt Panel</span>
  <a href="/logout" class="btn btn-outline-light">Logout</a>
</nav>
<div class="container py-4">
{{ content|safe }}
</div>
</body>
</html>
"""

# ================= Login =================
@app.route("/login", methods=["GET", "POST"])
def login():
    ip = request.remote_addr
    users = load_json(USERS_FILE, {})

    if request.method == "POST":
        u = request.form.get("username")
        p = request.form.get("password")

        if u in users and users[u]["password"] == hash_password(p):
            session["user"] = u
            log_event(f"LOGIN SUCCESS {u} IP:{ip}")
            return redirect("/dashboard")
        else:
            log_event(f"LOGIN FAIL {u} IP:{ip}")
            return "Invalid login"

    return f"""
<style>
body {{
background: url('/static/img/login_bg.jpg') center/cover no-repeat;
height:100vh; display:flex; justify-content:center; align-items:center;
}}
.box {{
background: rgba(2,6,23,.85);
padding:40px;
border-radius:20px;
width:360px;
animation: fadeIn .8s ease;
box-shadow:0 0 40px black;
}}
@keyframes fadeIn {{
from {{opacity:0; transform:translateY(30px)}}
to {{opacity:1; transform:translateY(0)}}
}}
input,button {{
width:100%; padding:12px; margin:8px 0;
border-radius:10px; border:none;
}}
button {{ background:#2563eb; color:white; font-weight:bold; }}
</style>

<form method="post" class="box">
  <div style="text-align:center;">
    <img src="/static/img/logo.png" width="90"><br><br>
    <h4>Rematch Egypt Admin</h4>
  </div>
  <input name="username" placeholder="Username">
  <input name="password" type="password" placeholder="Password">
  <button>Login</button>
</form>
"""

# ================= Dashboard =================
@app.route("/dashboard")
@login_required
def dashboard():
    keys = load_json(DB_FILE, {})
    content = f"""
    <div class="row g-4">
      <div class="col-md-4"><div class="card p-4 text-center">Total Keys<br><h2>{len(keys)}</h2></div></div>
      <div class="col-md-4"><div class="card p-4 text-center"><a href='/keys' class='btn btn-primary'>Manage Keys</a></div></div>
      <div class="col-md-4"><div class="card p-4 text-center"><a href='/export' class='btn btn-success'>Export CSV</a></div></div>
    </div>
    """
    return render_template_string(BASE_HTML, content=content)

# ================= Keys =================
@app.route("/keys")
@login_required
def keys():
    data = load_json(DB_FILE, {})
    rows = ""
    for k,v in data.items():
        rows += f"<tr><td>{k}</td><td>{v['hwid']}</td><td>{v['expires_in']}</td></tr>"
    content = f"""
    <h3>Keys</h3>
    <form method="post" action="/gen">
      <button class="btn btn-success">Generate Key</button>
    </form>
    <table class="table table-dark mt-3">
      <tr><th>Key</th><th>HWID</th><th>Days</th></tr>
      {rows}
    </table>
    """
    return render_template_string(BASE_HTML, content=content)

# ================= Generate =================
@app.route("/gen", methods=["POST"])
@login_required
def gen():
    data = load_json(DB_FILE, {})
    key = str(uuid.uuid4())[:8].upper()
    data[key] = {"hwid":None,"created_at":int(time.time()),"expires_in":30}
    save_json(DB_FILE, data)
    return redirect("/keys")

# ================= Export =================
@app.route("/export")
@admin_required
def export():
    data = load_json(DB_FILE,{})
    with open("export.csv","w",newline="") as f:
        w = csv.writer(f)
        w.writerow(["Key","HWID","Days"])
        for k,v in data.items():
            w.writerow([k,v["hwid"],v["expires_in"]])
    return send_file("export.csv", as_attachment=True)

# ================= API Check =================
@app.route("/check", methods=["POST"])
def check():
    req = request.json
    data = load_json(DB_FILE,{})
    key = req.get("key")
    hwid = req.get("hwid")
    if key not in data:
        return jsonify({"status":"invalid"})
    rec = data[key]
    if rec["hwid"] is None:
        rec["hwid"]=hwid
        save_json(DB_FILE,data)
        return jsonify({"status":"bound"})
    if rec["hwid"]==hwid:
        return jsonify({"status":"ok"})
    return jsonify({"status":"blocked"})

# ================= Logout =================
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
