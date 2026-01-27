from flask import Flask, request, jsonify, redirect, session, render_template_string
import json, os, uuid, time
from functools import wraps

app = Flask(__name__)
app.secret_key = "change-this-secret"

ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "123456"
DB_FILE = "keys.json"

# ----------------- Database -----------------
def load_db():
    if not os.path.exists(DB_FILE):
        return {}
    with open(DB_FILE, "r") as f:
        return json.load(f)

def save_db(data):
    with open(DB_FILE, "w") as f:
        json.dump(data, f, indent=4)

# ----------------- Auth -----------------
def login_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if not session.get("logged_in"):
            return redirect("/login")
        return f(*args, **kwargs)
    return wrapper

# ----------------- Layout -----------------
BASE_HTML = """
<!DOCTYPE html>
<html>
<head>
<title>Rematch Egypt Panel</title>
<link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/css/bootstrap.min.css" rel="stylesheet">
<link rel="stylesheet" href="https://cdn.datatables.net/1.13.6/css/jquery.dataTables.min.css">
<script src="https://code.jquery.com/jquery-3.7.0.min.js"></script>
<script src="https://cdn.datatables.net/1.13.6/js/jquery.dataTables.min.js"></script>

<style>
body {
    background: linear-gradient(135deg, #020617, #0b1220);
    color: #e2e8f0;
    font-family: 'Segoe UI', sans-serif;
}
.navbar {
    background: #020617;
    border-bottom: 1px solid #1f2937;
}
.card {
    background: #0f172a;
    border: 1px solid #1f2937;
    border-radius: 15px;
    box-shadow: 0 10px 30px rgba(0,0,0,.4);
}
.table { color: #e2e8f0; }
.btn-primary { background: #2563eb; border: none; }
.btn-success { background: #16a34a; border: none; }
</style>
</head>
<body>

<nav class="navbar navbar-dark px-4 py-3">
  <span class="navbar-brand fw-bold">🎮 Rematch Egypt Admin</span>
  <a href="/logout" class="btn btn-sm btn-outline-light">Logout</a>
</nav>

<div class="container py-4">
  {{ content|safe }}
</div>

</body>
</html>
"""

# ----------------- Login -----------------
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        if request.form.get("username") == ADMIN_USERNAME and request.form.get("password") == ADMIN_PASSWORD:
            session["logged_in"] = True
            return redirect("/dashboard")
        return "Invalid login"

    return f"""
    <style>
    body {{
        background: 
            linear-gradient(rgba(0,0,0,.75), rgba(0,0,0,.75)),
            url('/static/img/login_bg.jpg');
        background-size: cover;
        background-position: center;
        background-attachment: fixed;
        display:flex;
        align-items:center;
        justify-content:center;
        height:100vh;
        color:white;
        font-family:Segoe UI;
    }}
    .box {{
        background: rgba(2,6,23,.92);
        padding:40px;
        border-radius:20px;
        width:360px;
        border:1px solid #1f2937;
        box-shadow:0 0 50px rgba(0,0,0,.9);
        backdrop-filter: blur(6px);
    }}
    input,button {{
        width:100%;
        padding:14px;
        margin:10px 0;
        border-radius:12px;
        border:none;
        outline:none;
    }}
    input {{
        background:#020617;
        color:white;
        border:1px solid #1f2937;
    }}
    button {{
        background:linear-gradient(135deg,#2563eb,#38bdf8);
        color:white;
        font-weight:bold;
        letter-spacing:1px;
        transition:.3s;
    }}
    button:hover {{
        transform: translateY(-2px);
        box-shadow:0 0 20px #2563eb88;
    }}
    </style>

    <form method="post" class="box">
      <h3 style="text-align:center;margin-bottom:25px;">🎮 Rematch Egypt Admin</h3>
      <input name="username" placeholder="Username">
      <input name="password" type="password" placeholder="Password">
      <button>Login</button>
    </form>
    """

# ----------------- Dashboard -----------------
@app.route("/dashboard")
@login_required
def dashboard():
    data = load_db()
    now = int(time.time())
    total = len(data)
    active = expired = used = 0

    for v in data.values():
        lifetime = v["expires_in"] * 86400
        if now - v["created_at"] > lifetime:
            expired += 1
        else:
            active += 1
        if v["hwid"]:
            used += 1

    content = f"""
    <div class="row g-4">
      <div class="col-md-3"><div class="card p-4 text-center"><h6>Total Keys</h6><h2>{total}</h2></div></div>
      <div class="col-md-3"><div class="card p-4 text-center"><h6>Active</h6><h2>{active}</h2></div></div>
      <div class="col-md-3"><div class="card p-4 text-center"><h6>Expired</h6><h2>{expired}</h2></div></div>
      <div class="col-md-3"><div class="card p-4 text-center"><h6>Used</h6><h2>{used}</h2></div></div>
    </div>
    <div class="mt-4">
      <a href="/keys" class="btn btn-primary">Manage Keys</a>
    </div>
    """
    return render_template_string(BASE_HTML, content=content)

# ----------------- Keys Page -----------------
@app.route("/keys")
@login_required
def keys_page():
    data = load_db()
    now = int(time.time())
    rows = ""

    for k, v in data.items():
        lifetime = v["expires_in"] * 86400
        status = "Expired" if now - v["created_at"] > lifetime else "Active"
        rows += f"<tr><td>{k}</td><td>{v['hwid'] or '-'}</td><td>{v['expires_in']} days</td><td>{status}</td></tr>"

    content = f"""
    <h3 class="mb-3">Keys Manager</h3>

    <form method="post" action="/gen" class="mb-4">
      <select name="days" class="form-select w-25 d-inline">
        <option value="7">7 Days</option>
        <option value="30" selected>30 Days</option>
        <option value="90">90 Days</option>
        <option value="9999">Lifetime</option>
      </select>
      <button class="btn btn-success ms-2">Generate</button>
    </form>

    <table id="keysTable" class="display">
      <thead>
        <tr><th>Key</th><th>HWID</th><th>Duration</th><th>Status</th></tr>
      </thead>
      <tbody>{rows}</tbody>
    </table>

    <script>
      $(document).ready(function() {{
        $('#keysTable').DataTable();
      }});
    </script>
    """
    return render_template_string(BASE_HTML, content=content)

# ----------------- Generate -----------------
@app.route("/gen", methods=["POST"])
@login_required
def generate():
    days = int(request.form.get("days", 30))
    data = load_db()
    key = str(uuid.uuid4())[:8].upper()
    data[key] = {"hwid": None, "created_at": int(time.time()), "expires_in": days}
    save_db(data)
    return redirect("/keys")

# ----------------- API -----------------
@app.route("/check", methods=["POST"])
def check():
    req = request.json
    key, hwid = req.get("key"), req.get("hwid")
    data = load_db()

    if key not in data:
        return jsonify({"status": "invalid"})

    record = data[key]
    now = int(time.time())
    lifetime = record["expires_in"] * 86400

    if now - record["created_at"] > lifetime:
        return jsonify({"status": "expired"})

    if record["hwid"] is None:
        record["hwid"] = hwid
        save_db(data)
        return jsonify({"status": "bound"})

    if record["hwid"] == hwid:
        return jsonify({"status": "ok"})

    return jsonify({"status": "blocked"})

# ----------------- Logout -----------------
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
