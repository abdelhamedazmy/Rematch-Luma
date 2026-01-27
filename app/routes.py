from flask import Blueprint, render_template, session, redirect, request, jsonify
from .db import get_db, add_log
import uuid

main_bp = Blueprint("main", __name__)

# ================= Helpers =================
def login_required():
    return session.get("user")

def admin_required():
    return session.get("role") == "admin"

def get_ip():
    return request.headers.get("X-Forwarded-For", request.remote_addr)


# ================= Home =================
@main_bp.route("/")
def home():
    return redirect("/dashboard")


# ================= Dashboard =================
@main_bp.route("/dashboard")
def dashboard():
    if not login_required():
        return redirect("/login")

    db = get_db()

    users_count = db.execute("SELECT COUNT(*) FROM users").fetchone()[0]
    keys_count = db.execute("SELECT COUNT(*) FROM keys").fetchone()[0]
    active_keys = db.execute("SELECT COUNT(*) FROM keys WHERE hwid IS NOT NULL").fetchone()[0]

    return render_template(
        "dashboard.html",
        title="Rematch Egypt Control Panel",
        user=session["user"],
        role=session["role"],
        users_count=users_count,
        keys_count=keys_count,
        active_keys=active_keys
    )


# ================= Keys Page =================
@main_bp.route("/keys")
def keys():
    if not login_required():
        return redirect("/login")

    db = get_db()
    keys = db.execute("SELECT * FROM keys").fetchall()

    return render_template("keys.html", keys=keys, role=session["role"])


# ================= Generate Key (Admin only) =================
@main_bp.route("/keys/generate", methods=["GET", "POST"])
def generate_key():
    if not login_required():
        return redirect("/login")

    if not admin_required():
        return "Forbidden", 403

    new_key = str(uuid.uuid4())[:10].upper()

    db = get_db()
    db.execute(
        "INSERT INTO keys (key, hwid, days) VALUES (?, ?, ?)",
        (new_key, None, 30)
    )
    db.commit()

    # LOG
    add_log(session["user"], f"Generated key: {new_key}", get_ip())

    return redirect("/keys")


# ================= Delete Key (Admin only) =================
@main_bp.route("/keys/delete/<int:key_id>")
def delete_key(key_id):
    if not login_required():
        return redirect("/login")

    if not admin_required():
        return "Forbidden", 403

    db = get_db()

    key_row = db.execute("SELECT key FROM keys WHERE id = ?", (key_id,)).fetchone()
    if key_row:
        add_log(session["user"], f"Deleted key: {key_row['key']}", get_ip())

    db.execute("DELETE FROM keys WHERE id = ?", (key_id,))
    db.commit()

    return redirect("/keys")


# ================= API FOR EXE =================
@main_bp.route("/check", methods=["POST"])
def api_check():
    data = request.get_json()

    if not data:
        return jsonify({"status": "error", "message": "No data"}), 400

    key = data.get("key")
    hwid = data.get("hwid")

    if not key or not hwid:
        return jsonify({"status": "error", "message": "Missing key or hwid"}), 400

    db = get_db()
    row = db.execute("SELECT * FROM keys WHERE key = ?", (key,)).fetchone()

    # Key مش موجود
    if not row:
        add_log("API", f"Invalid key attempt: {key}", get_ip())
        return jsonify({"status": "invalid"})

    # أول استخدام → اربط HWID
    if row["hwid"] is None:
        db.execute("UPDATE keys SET hwid = ? WHERE id = ?", (hwid, row["id"]))
        db.commit()

        add_log("API", f"Key bound: {key} → {hwid}", get_ip())
        return jsonify({"status": "bound"})

    # نفس الجهاز
    if row["hwid"] == hwid:
        add_log("API", f"Key OK: {key}", get_ip())
        return jsonify({"status": "ok"})

    # جهاز مختلف
    add_log("API", f"Blocked key: {key} (HWID mismatch)", get_ip())
    return jsonify({"status": "blocked"})
# ================= Users Management =================
@main_bp.route("/users")
def users_page():
    if not login_required():
        return redirect("/login")

    if not admin_required():
        return "Forbidden", 403

    db = get_db()
    users = db.execute("SELECT * FROM users").fetchall()

    return render_template("users.html", users=users)


@main_bp.route("/users/create", methods=["POST"])
def create_user():
    if not login_required() or not admin_required():
        return "Forbidden", 403

    username = request.form.get("username")
    password = request.form.get("password")
    role = request.form.get("role")

    if not username or not password or not role:
        return redirect("/users")

    db = get_db()
    try:
        db.execute(
            "INSERT INTO users (username, password, role) VALUES (?, ?, ?)",
            (username, password, role)
        )
        db.commit()
    except:
        pass  # لو اليوزر موجود بالفعل

    return redirect("/users")


@main_bp.route("/users/delete/<int:user_id>")
def delete_user(user_id):
    if not login_required() or not admin_required():
        return "Forbidden", 403

    db = get_db()
    db.execute("DELETE FROM users WHERE id = ?", (user_id,))
    db.commit()

    return redirect("/users")


@main_bp.route("/users/toggle_role/<int:user_id>")
def toggle_role(user_id):
    if not login_required() or not admin_required():
        return "Forbidden", 403

    db = get_db()
    user = db.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()

    if not user:
        return redirect("/users")

    new_role = "admin" if user["role"] == "viewer" else "viewer"

    db.execute("UPDATE users SET role = ? WHERE id = ?", (new_role, user_id))
    db.commit()

    return redirect("/users")
# ================= Logs Viewer (Admin only) =================
@main_bp.route("/logs")
def logs_page():
    if not login_required():
        return redirect("/login")

    if not admin_required():
        return "Forbidden", 403

    db = get_db()
    logs = db.execute(
        "SELECT * FROM logs ORDER BY id DESC"
    ).fetchall()

    return render_template("logs.html", logs=logs)





