from flask import Flask, request, jsonify, render_template_string, redirect, session
import json, os, uuid, time
from functools import wraps

app = Flask(__name__)
app.secret_key = "super-secret-key-change-me"

ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "123456"

DB_FILE = "keys.json"

# ===================== Database =====================
def load_db():
    if not os.path.exists(DB_FILE):
        return {}
    with open(DB_FILE, "r") as f:
        return json.load(f)

def save_db(data):
    with open(DB_FILE, "w") as f:
        json.dump(data, f, indent=4)

# ===================== Auth =====================
def login_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if not session.get("logged_in"):
            return redirect("/login")
        return f(*args, **kwargs)
    return wrapper

# ===================== Login =====================
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        u = request.form.get("username")
        p = request.form.get("password")
        if u == ADMIN_USERNAME and p == ADMIN_PASSWORD:
            session["logged_in"] = True
            return redirect("/dashboard")
        return "Invalid login"

    return """
    <h2>Rematch Egypt Admin</h2>
    <form method="post">
      <input name="username" placeholder="Username"><br><br>
      <input name="password" type="password" placeholder="Password"><br><br>
      <button>Login</button>
    </form>
    """

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")

# ===================== Dashboard =====================
@app.route("/dashboard")
@login_required
def dashboard():
    data = load_db()

    total = len(data)
    active = 0
    expired = 0
    used = 0

    now = int(time.time())

    for k, v in data.items():
        lifetime = v["expires_in"] * 86400
        if now - v["created_at"] > lifetime:
            expired += 1
        else:
            active += 1
        if v["hwid"]:
            used += 1

    return f"""
    <h1>Dashboard</h1>
    <ul>
      <li>Total Keys: {total}</li>
      <li>Active: {active}</li>
      <li>Expired: {expired}</li>
      <li>Used: {used}</li>
    </ul>
    <a href="/keys">Manage Keys</a> | <a href="/logout">Logout</a>
    """

# ===================== Generate Key =====================
@app.route("/gen", methods=["POST"])
@login_required
def generate_key():
    days = int(request.form.get("days", 30))
    data = load_db()

    key = str(uuid.uuid4())[:8].upper()
    data[key] = {
        "hwid": None,
        "created_at": int(time.time()),
        "expires_in": days
    }

    save_db(data)
    return redirect("/keys")

# ===================== Keys Table =====================
@app.route("/keys")
@login_required
def keys_page():
    data = load_db()

    rows = ""
    now = int(time.time())

    for k, v in data.items():
        lifetime = v["expires_in"] * 86400
        status = "Expired" if now - v["created_at"] > lifetime else "Active"
        rows += f"""
        <tr>
          <td>{k}</td>
          <td>{v['hwid'] or '-'}</td>
          <td>{v['expires_in']} days</td>
          <td>{status}</td>
        </tr>
        """

    return f"""
<!DOCTYPE html>
<html>
<head>
  <title>Keys Manager</title>
  <link rel="stylesheet" href="https://cdn.datatables.net/1.13.6/css/jquery.dataTables.min.css">
</head>
<body>
<h2>Keys Manager</h2>

<form method="post" action="/gen">
  Generate key for:
  <select name="days">
    <option value="7">7 days</option>
    <option value="30" selected>30 days</option>
    <option value="90">90 days</option>
    <option value="9999">Lifetime</option>
  </select>
  <button>Generate</button>
</form>

<br>

<table id="keysTable">
<thead>
<tr><th>Key</th><th>HWID</th><th>Duration</th><th>Status</th></tr>
</thead>
<tbody>
{rows}
</tbody>
</table>

<br>
<a href="/dashboard">Back to Dashboard</a>

<script src="https://code.jquery.com/jquery-3.7.0.min.js"></script>
<script src="https://cdn.datatables.net/1.13.6/js/jquery.dataTables.min.js"></script>
<script>
$(document).ready(function() {{
    $('#keysTable').DataTable();
}});
</script>
</body>
</html>
"""

# ===================== Client Check =====================
@app.route("/check", methods=["POST"])
def check_key():
    req = request.json
    key = req.get("key")
    hwid = req.get("hwid")

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

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
