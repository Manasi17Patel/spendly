from flask import Flask, render_template, request, redirect, url_for, flash
from database.db import get_db, init_db, seed_db, create_user

app = Flask(__name__)
app.secret_key = 'dev-secret-key-change-in-production'  # In production, use a strong secret key from environment variables

# Initialize database on app startup
with app.app_context():
    init_db()
    seed_db()


# ------------------------------------------------------------------ #
# Routes                                                              #
# ------------------------------------------------------------------ #

@app.route("/")
def landing():
    return render_template("landing.html")


@app.route("/register")
def register():
    return render_template("register.html")


@app.route("/register", methods=["POST"])
def register_post():
    name = request.form.get("name", "").strip()
    email = request.form.get("email", "").strip()
    password = request.form.get("password", "")

    # Validation
    if not name:
        flash("Name is required", "error")
        return render_template("register.html"), 400

    if not email:
        flash("Email is required", "error")
        return render_template("register.html"), 400

    if not password or len(password) < 8:
        flash("Password must be at least 8 characters long", "error")
        return render_template("register.html"), 400

    # Basic email format check
    if "@" not in email or "." not in email.split("@")[-1]:
        flash("Please enter a valid email address", "error")
        return render_template("register.html"), 400

    # Attempt to create user
    user_id = create_user(name, email, password)

    if user_id is None:
        flash("Email already registered. Please use a different email.", "error")
        return render_template("register.html"), 400

    # Success
    flash("Account created successfully! Please log in.", "success")
    return redirect(url_for("login"))


@app.route("/login")
def login():
    return render_template("login.html")


@app.route("/terms")
def terms():
    return render_template("terms.html")


@app.route("/privacy")
def privacy():
    return render_template("privacy.html")


# ------------------------------------------------------------------ #
# Placeholder routes — students will implement these                  #
# ------------------------------------------------------------------ #

@app.route("/logout")
def logout():
    return "Logout — coming in Step 3"


@app.route("/profile")
def profile():
    return "Profile page — coming in Step 4"


@app.route("/expenses/add")
def add_expense():
    return "Add expense — coming in Step 7"


@app.route("/expenses/<int:id>/edit")
def edit_expense(id):
    return "Edit expense — coming in Step 8"


@app.route("/expenses/<int:id>/delete")
def delete_expense(id):
    return "Delete expense — coming in Step 9"


if __name__ == "__main__":
    app.run(debug=True, port=5001)
