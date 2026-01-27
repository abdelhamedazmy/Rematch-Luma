from flask import Blueprint, render_template, session, redirect, request
from .db import get_db
import uuid

main_bp = Blueprint("main", __name__)

# ================= Helpers =================
def login_required():
    return session.get("user")

def admin_required():
    return session.get("role") == "admin"


# ================= Home =================
@main_bp.route("/")
def home():
    return redirect("/dashboard")


# ================= Dashboard =================
@main_bp.route("/dashboard")
def dashboard():
    if not login_required():
        return redirect("/login")

    return render_template(
        "dashboard.html",
        title="Rematch Egypt Control Panel",
        user=session["user"],
        role=session["role"]
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
    if not session.get("user"):
        return redirect("/login")

    if session.get("role") != "admin":
        return "Forbidden", 403

    new_key = str(uuid.uuid4())[:10].upper()

    db = get_db()
    db.execute(
        "INSERT INTO keys (key, hwid, days) VALUES (?, ?, ?)",
        (new_key, None, 30)
    )
    db.commit()

    return redirect("/keys")



# ================= Delete Key (Admin only) =================
@main_bp.route("/keys/delete/<int:key_id>")
def delete_key(key_id):
    if not login_required():
        return redirect("/login")

    if not admin_required():
        return "Forbidden", 403

    db = get_db()
    db.execute("DELETE FROM keys WHERE id = ?", (key_id,))
    db.commit()

    return redirect("/keys")

