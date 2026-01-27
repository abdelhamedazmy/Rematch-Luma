from flask import Flask, request, jsonify
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


# ===== توليد Key بمدة (افتراضي 7 أيام) =====
@app.route("/gen", methods=["POST"])
def generate_key():
    data = load_db()

    new_key = str(uuid.uuid4())[:8].upper()

    data[new_key] = {
        "hwid": None,
        "created_at": int(time.time()),
        "expires_in": 30  # أيام
    }

    save_db(data)
    return jsonify({"key": new_key, "expires_in_days": 30})


# ===== التحقق من key =====
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


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
