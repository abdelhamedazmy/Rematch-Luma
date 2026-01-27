from flask import Blueprint, render_template, request, redirect, session
from .db import get_db

auth_bp = Blueprint("auth", __name__)

@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        u = request.form["username"]
        p = request.form["password"]

        db = get_db()
        user = db.execute("SELECT * FROM users WHERE username=? AND password=?", (u, p)).fetchone()

        if user:
            session["user"] = u
            session["role"] = user["role"]
            return redirect("/dashboard")

        return "Invalid Login"

    return render_template("login.html")


@auth_bp.route("/logout")
def logout():
    session.clear()
    return redirect("/login")
