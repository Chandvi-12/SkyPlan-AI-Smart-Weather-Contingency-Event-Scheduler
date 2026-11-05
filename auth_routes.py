import functools
from flask import (
    Blueprint, render_template, request, redirect, url_for, flash, session, g
)
from app.models.user_model import UserModel

auth_bp = Blueprint("auth", __name__, url_prefix="/auth")

def login_required(view):
    @functools.wraps(view)
    def wrapped_view(**kwargs):
        if session.get("user_id") is None:
            flash("Please sign in to access SkyPlan AI.", "warning")
            return redirect(url_for("auth.login", next=request.url))
        return view(**kwargs)
    return wrapped_view

@auth_bp.before_app_request
def load_logged_in_user():
    user_id = session.get("user_id")
    if user_id is None:
        g.user = None
    else:
        g.user = UserModel.find_by_id(user_id)

@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if g.user:
        return redirect(url_for("dashboard.index"))

    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "")
        confirm_password = request.form.get("confirm_password", "")

        errors = []
        if not name:
            errors.append("Full name is required.")
        if not email or "@" not in email:
            errors.append("A valid email address is required.")
        if not password or len(password) < 6:
            errors.append("Password must be at least 6 characters.")
        if password != confirm_password:
            errors.append("Passwords do not match.")

        if errors:
            for err in errors:
                flash(err, "danger")
            return render_template("auth/register.html", name=name, email=email)

        user, err = UserModel.create_user(name, email, password)
        if err:
            flash(err, "danger")
            return render_template("auth/register.html", name=name, email=email)

        flash("Account successfully created! Please sign in with your credentials.", "success")
        return redirect(url_for("auth.login"))

    return render_template("auth/register.html")

@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if g.user:
        return redirect(url_for("dashboard.index"))

    if request.method == "POST":
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "")

        if not email or not password:
            flash("Please provide both email and password.", "danger")
            return render_template("auth/login.html", email=email)

        user = UserModel.find_by_email(email)
        if user and UserModel.verify_password(user["password_hash"], password):
            session.clear()
            session["user_id"] = str(user["_id"])
            session["user_name"] = user["name"]
            session["user_email"] = user["email"]
            flash(f"Welcome back, {user['name']}!", "success")
            
            next_page = request.args.get("next")
            if next_page and not next_page.startswith("//") and not next_page.startswith("http"):
                return redirect(next_page)
            return redirect(url_for("dashboard.index"))

        flash("Invalid email or password. Please try again.", "danger")
        return render_template("auth/login.html", email=email)

    return render_template("auth/login.html")

@auth_bp.route("/logout")
def logout():
    session.clear()
    flash("You have been signed out successfully.", "info")
    return redirect(url_for("auth.login"))

@auth_bp.route("/profile", methods=["GET", "POST"])
@login_required
def profile():
    user = g.user
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        new_password = request.form.get("new_password", "")
        confirm_password = request.form.get("confirm_password", "")

        if not name:
            flash("Name cannot be empty.", "danger")
            return render_template("auth/profile.html", user=user)

        if new_password:
            if len(new_password) < 6:
                flash("Password must be at least 6 characters.", "danger")
                return render_template("auth/profile.html", user=user)
            if new_password != confirm_password:
                flash("New passwords do not match.", "danger")
                return render_template("auth/profile.html", user=user)

        UserModel.update_profile(user["_id"], name, new_password if new_password else None)
        flash("Profile updated successfully!", "success")
        return redirect(url_for("auth.profile"))

    return render_template("auth/profile.html", user=user)

