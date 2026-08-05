import os
from flask import Flask, render_template, request, redirect, url_for, flash, session
from database.db import init_db, seed_db, create_user, get_user_by_email, verify_password
from database.queries import get_user_by_id as get_profile_user_by_id, get_summary_stats
from database.queries import get_recent_transactions, get_category_breakdown

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

    user_id = session["user_id"]

    def _format_inr(amount):
        """Format a numeric amount as ₹ with thousands separator and 2 decimals."""
        return f"₹{amount:,.2f}"

    # === SUBAGENT 2: USER INFO (START) ===
    _user = get_profile_user_by_id(user_id)
    if _user is None:
        session.clear()
        flash("Your session has expired. Please log in again.", "warning")
        return redirect(url_for("login"))
    # === SUBAGENT 2: USER INFO (END) ===

    # === SUBAGENT 2: SUMMARY STATS (START) ===
    _stats = get_summary_stats(user_id)
    _stats_list = [
        {'label': 'Total Spent', 'value': _format_inr(_stats['total_spent']), 'icon': '💰'},
        {'label': 'Transactions', 'value': str(_stats['transaction_count']), 'icon': '📊'},
        {'label': 'Top Category', 'value': _stats['top_category'], 'icon': '🍔'},
    ]
    # === SUBAGENT 2: SUMMARY STATS (END) ===

    # === SUBAGENT 1: TRANSACTION HISTORY (START) ===
    _transactions = [
        {
            'date': tx['date'],
            'desc': tx['description'],
            'category': tx['category'],
            'amount': _format_inr(tx['amount']),
        }
        for tx in get_recent_transactions(user_id, limit=10)
    ]
    # === SUBAGENT 1: TRANSACTION HISTORY (END) ===

    # === SUBAGENT 3: CATEGORY BREAKDOWN (START) ===
    _categories = [
        {
            'name': cat['name'],
            'amount': _format_inr(cat['amount']),
            'percentage': cat['pct'],
        }
        for cat in get_category_breakdown(user_id)
    ]
    # === SUBAGENT 3: CATEGORY BREAKDOWN (END) ===

    profile_data = {
        'user': _user,
        'stats': _stats_list,
        'transactions': _transactions,
        'categories': _categories,
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
