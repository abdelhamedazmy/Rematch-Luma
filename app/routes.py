from flask import Blueprint, render_template, session, redirect

main_bp = Blueprint("main", __name__)

@main_bp.route("/")
def home():
    return redirect("/login")

@main_bp.route("/dashboard")
def dashboard():
    if not session.get("user"):
        return redirect("/login")

    return render_template(
        "dashboard.html",
        title="Rematch Egypt Control Panel",
        user=session["user"],
        role=session["role"]
    )
