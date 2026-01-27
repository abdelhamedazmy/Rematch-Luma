ADMIN_PASSWORD = "123456"

from flask import Flask, request, jsonify, render_template_string
import json
import os
import uuid
import time

app = Flask(__name__)

DB_FILE = "keys.json"


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
        "expires_in": 30  # مدة الصلاحية بالأيام
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

    # تحقق من الانتهاء
    now = int(time.time())
    lifetime = record["expires_in"] * 86400

    if now - record["created_at"] > lifetime:
        return jsonify({"status": "expired"})

    # أول استخدام
    if record["hwid"] is None:
        record["hwid"] = hwid
        save_db(data)
        return jsonify({"status": "bound"})

    # نفس الجهاز
    if record["hwid"] == hwid:
        return jsonify({"status": "ok"})

    # جهاز مختلف
    return jsonify({"status": "blocked"})


# ================= صفحة توليد Keys من المتصفح =================
@app.route("/admin", methods=["GET", "POST"])
def admin_panel():
    generated_key = None

    if request.method == "POST":
        data = load_db()

        new_key = str(uuid.uuid4())[:8].upper()
        data[new_key] = {
            "hwid": None,
            "created_at": int(time.time()),
            "expires_in": 30
        }

        save_db(data)
        generated_key = new_key

    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Rematch Egypt - Key Generator</title>
        <style>
            body {
                background: #0f172a;
                color: white;
                font-family: Arial;
                display: flex;
                justify-content: center;
                align-items: center;
                height: 100vh;
            }
            .box {
                background: #111827;
                padding: 30px;
                border-radius: 15px;
                text-align: center;
                box-shadow: 0 0 20px #00ffd5;
            }
            button {
                background: #ff0055;
                color: white;
                border: none;
                padding: 12px 25px;
                border-radius: 10px;
                font-size: 16px;
                cursor: pointer;
            }
            .key {
                margin-top: 15px;
                font-size: 22px;
                color: #00ffd5;
                font-weight: bold;
            }
        </style>
    </head>
    <body>
        <div class="box">
            <h2>🎮 Rematch Egypt Key Generator</h2>
            <form method="post">
                <button type="submit">Generate New Key</button>
            </form>

            {% if key %}
            <div class="key">🔑 {{ key }}</div>
            {% endif %}
        </div>
    </body>
    </html>
    """

    return render_template_string(html, key=generated_key)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)

