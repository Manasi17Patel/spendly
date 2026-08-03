import os
from flask import Flask, render_template, request, redirect, url_for, flash, session
from database.db import get_db, init_db, seed_db, create_user, get_user_by_email, verify_password, get_user_by_id

app = Flask(__name__)
app.secret_key = 'dev-secret-key-change-in-production'  # In production, use a strong secret key from environment variables

# Initialize database on app startup only if not in testing
if os.environ.get('FLASK_ENV') != 'testing':
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
    if 'user_id' in session:
        return redirect(url_for("landing"))
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
    if 'user_id' in session:
        return redirect(url_for("landing"))
    return render_template("login.html")


@app.route("/login", methods=["POST"])
def login_post():
    email = request.form.get("email", "").strip()
    password = request.form.get("password", "")

    # Validation
    if not email:
        flash("Email is required", "error")
        return render_template("login.html"), 400

    if not password:
        flash("Password is required", "error")
        return render_template("login.html"), 400

    # Get user by email
    user = get_user_by_email(email)
    if not user:
        flash("Invalid email or password", "error")
        return render_template("login.html"), 400

    # Verify password
    if not verify_password(user["password_hash"], password):
        flash("Invalid email or password", "error")
        return render_template("login.html"), 400

    # Success - log user in
    session["user_id"] = user["id"]
    flash("Logged in successfully!", "success")
    return redirect(url_for("profile"))


@app.route("/terms")
def terms():
    return render_template("terms.html")


@app.route("/privacy")
def privacy():
    return render_template("privacy.html")


@app.route("/profile")
def profile():
    # Check if user is logged in
    if "user_id" not in session:
        flash("Please log in to view your profile.", "info")
        return redirect(url_for("login"))

    # Get user from database (in Step 4 we'll use hardcoded data, but let's get real user data for consistency)
    user_id = session["user_id"]
    user = get_user_by_id(user_id)

    # If user not found (shouldn't happen if session is valid), log them out
    if user is None:
        session.clear()
        flash("Your session has expired. Please log in again.", "warning")
        return redirect(url_for("login"))

    # For Step 4, we'll use hardcoded mock data for the profile view
    # In a real implementation, we would query the database for stats, transactions, etc.
    # But for now, we'll pass the real user data and some mock data for the UI

    # Mock data for profile view (will be replaced with real queries in later steps)
    profile_data = {
        'user': {
            'name': user['name'],
            'email': user['email'],
            'member_since': user['created_at'].split('-')[0] + " " +
                          ["January", "February", "March", "April", "May", "June",
                           "July", "August", "September", "October", "November", "December"][
                              int(user['created_at'].split('-')[1]) - 1] if user['created_at'] and '-' in user['created_at'] else "January 2026"
        },
        'stats': [
            {'label': 'Total Spent', 'value': '₹2,450.00', 'icon': '💰'},
            {'label': 'Transactions', 'value': '24', 'icon': '📊'},
            {'label': 'Top Category', 'value': 'Food', 'icon': '🍔'}
        ],
        'transactions': [
            {'date': '2026-07-20', 'desc': 'Grocery shopping', 'category': 'Food', 'amount': '₹1,200.00'},
            {'date': '2026-07-18', 'desc': 'Metro pass', 'category': 'Transport', 'amount': '₹800.00'},
            {'date': '2026-07-15', 'desc': 'Electricity bill', 'category': 'Bills', 'amount': '₹1,500.00'},
            {'date': '2026-07-10', 'desc': 'Movie tickets', 'category': 'Entertainment', 'amount': '₹400.00'},
            {'date': '2026-07-05', 'desc': 'Pharmacy', 'category': 'Health', 'amount': '₹350.00'}
        ],
        'categories': [
            {'name': 'Food', 'amount': '₹1,200.00', 'percentage': 40},
            {'name': 'Transport', 'amount': '₹800.00', 'percentage': 27},
            {'name': 'Bills', 'amount': '₹1,500.00', 'percentage': 50},
            {'name': 'Entertainment', 'amount': '₹400.00', 'percentage': 13},
            {'name': 'Health', 'amount': '₹350.00', 'percentage': 12}
        ]
    }

    return render_template("profile.html", **profile_data)


# ------------------------------------------------------------------ #
# Placeholder routes — students will implement these                  #
# ------------------------------------------------------------------ #

@app.route("/logout")
def logout():
    session.clear()  # Clear all session data
    flash("You have been logged out", "info")
    return redirect(url_for("landing"))





if __name__ == "__main__":
    app.run(debug=True, port=5001)
