from flask import Flask, request, jsonify, render_template_string
import json
import os
import uuid
import time

# ===== إعدادات =====
ADMIN_PASSWORD = "123456"   # غيرها لأي باسورد تحبه
DB_FILE = "keys.json"

app = Flask(__name__)


def load_db():
    if not os.path.exists(DB_FILE):
        return {}
    with open(DB_FILE, "r") as f:
        return json.load(f)


def save_db(data):
    with open(DB_FILE, "w") as f:
        json.dump(data, f, indent=4)


# ================= توليد Key عبر API =================
@app.route("/gen", methods=["POST"])
def generate_key():
    data = load_db()

    new_key = str(uuid.uuid4())[:8].upper()

    data[new_key] = {
        "hwid": None,
        "created_at": int(time.time()),
        "expires_in": 30
    }

    save_db(data)
    return jsonify({"key": new_key, "expires_in_days": 30})


# ================= التحقق من Key =================
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


# ================= لوحة التحكم الاحترافية =================
@app.route("/admin", methods=["GET", "POST"])
def admin_panel():
    password = request.args.get("password")

    if password != ADMIN_PASSWORD:
        return "Unauthorized", 403

    data = load_db()

    # توليد key جديد
    if request.method == "POST" and request.form.get("action") == "generate":
        new_key = str(uuid.uuid4())[:8].upper()
        data[new_key] = {
            "hwid": None,
            "created_at": int(time.time()),
            "expires_in": 30
        }
        save_db(data)

    # حذف key
    if request.method == "POST" and request.form.get("action") == "delete":
        key_to_delete = request.form.get("key")
        if key_to_delete in data:
            del data[key_to_delete]
            save_db(data)

    # تجهيز الجدول
    rows = ""
    now = int(time.time())

    for key, info in data.items():
        status = "🟢 Active"

        if info["hwid"]:
            status = "🟡 Used"

        if now - info["created_at"] > info["expires_in"] * 86400:
            status = "🔴 Expired"

        rows += f"""
        <tr>
            <td>{key}</td>
            <td>{info["hwid"] or "-"}</td>
            <td>{status}</td>
            <td>
                <form method="post" style="display:inline;">
                    <input type="hidden" name="action" value="delete">
                    <input type="hidden" name="key" value="{key}">
                    <button>❌ Delete</button>
                </form>
            </td>
        </tr>
        """

    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Rematch Egypt Dashboard</title>
        <style>
            body {{ background:#0f172a; color:white; font-family:Arial; }}
            .box {{ padding:20px; }}
            table {{ width:100%; border-collapse: collapse; margin-top:15px; }}
            th, td {{ padding:10px; border-bottom:1px solid #333; text-align:center; }}
            button {{ background:#ff0055; color:white; border:none; padding:6px 12px; border-radius:6px; cursor:pointer; }}
            h1 {{ color:#00ffd5; }}
        </style>
    </head>
    <body>
        <div class="box">
            <h1>🎮 Rematch Egypt Admin Panel</h1>

            <form method="post">
                <input type="hidden" name="action" value="generate">
                <button>➕ Generate New Key</button>
            </form>

            <table>
                <tr>
                    <th>Key</th>
                    <th>HWID</th>
                    <th>Status</th>
                    <th>Action</th>
                </tr>
                {rows}
            </table>
        </div>
    </body>
    </html>
    """

    return html


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
