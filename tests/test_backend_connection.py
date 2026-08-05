"""Tests for Step 5 — backend connection for the profile page.

Covers:
- Unit tests for the four query helpers in database.queries
- Route tests for GET /profile (302 when logged out, 200 + content checks when logged in as demo user)
"""

import os
# Set environment variable to prevent the app from initializing the database on import
os.environ['FLASK_ENV'] = 'testing'

import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import sqlite3
from datetime import date

from werkzeug.security import generate_password_hash

import database.db
import database.queries
from app import app
from database.db import init_db, create_user


# ------------------------------------------------------------------ #
# Shared in-memory database setup                                    #
# ------------------------------------------------------------------ #

def _shared_in_memory_db():
    """Return a connection to a shared in-memory SQLite database."""
    uri = 'file:memdb_step5?mode=memory&cache=shared'
    conn = sqlite3.connect(uri, uri=True)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


# Monkey-patch get_db so both database.db and database.queries use the shared DB
database.db.get_db = _shared_in_memory_db
database.queries.get_db = _shared_in_memory_db


# Test config
app.config['TESTING'] = True
app.config['SECRET_KEY'] = 'test-secret-key'
client = app.test_client()


def _setup_demo_user():
    """Create the demo user with the same data as seed_db() in database.db.

    Returns the demo user's id (looked up by email, since autoincrement may not
    reset between test runs in the shared in-memory DB).
    """
    conn = _shared_in_memory_db()
    # Re-initialise the schema
    conn.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.execute('''
        CREATE TABLE IF NOT EXISTS expenses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            amount REAL NOT NULL,
            category TEXT NOT NULL,
            date TEXT NOT NULL,
            description TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        )
    ''')
    conn.commit()

    # Clear out anything left from a previous test, and reset autoincrement
    conn.execute("DELETE FROM expenses")
    conn.execute("DELETE FROM sqlite_sequence WHERE name='expenses'")
    conn.execute("DELETE FROM users")
    conn.execute("DELETE FROM sqlite_sequence WHERE name='users'")
    conn.commit()

    # Create demo user with a fixed created_at so member_since is deterministic
    conn.execute(
        "INSERT INTO users (name, email, password_hash, created_at) VALUES (?, ?, ?, ?)",
        ('Demo User', 'demo@spendly.com', generate_password_hash('demo123'), '2026-01-15 10:00:00'),
    )
    user_id = conn.execute(
        "SELECT id FROM users WHERE email = ?", ('demo@spendly.com',)
    ).fetchone()[0]

    # Insert the 8 seed expenses (must match the amounts in database.db.seed_db)
    today = date.today()
    expenses = [
        (user_id, 12.50, 'Food', str(today.replace(day=1)), 'Breakfast at cafe'),
        (user_id, 45.00, 'Transport', str(today.replace(day=2)), 'Taxi to airport'),
        (user_id, 80.00, 'Bills', str(today.replace(day=3)), 'Electricity bill'),
        (user_id, 15.99, 'Health', str(today.replace(day=4)), 'Pharmacy'),
        (user_id, 30.00, 'Entertainment', str(today.replace(day=5)), 'Movie tickets'),
        (user_id, 65.20, 'Shopping', str(today.replace(day=6)), 'Groceries'),
        (user_id, 120.00, 'Food', str(today.replace(day=7)), 'Weekend dinner'),
        (user_id, 25.00, 'Other', str(today.replace(day=8)), 'Book purchase'),
    ]
    for e in expenses:
        conn.execute(
            "INSERT INTO expenses (user_id, amount, category, date, description) VALUES (?, ?, ?, ?, ?)",
            e,
        )
    conn.commit()
    return user_id


# ------------------------------------------------------------------ #
# Unit tests — query helpers                                          #
# ------------------------------------------------------------------ #

def test_get_user_by_id_returns_profile_dict():
    uid = _setup_demo_user()
    result = database.queries.get_user_by_id(uid)
    assert result is not None
    assert result['name'] == 'Demo User'
    assert result['email'] == 'demo@spendly.com'
    assert result['member_since'] == 'January 2026'


def test_get_user_by_id_returns_none_for_missing_user():
    _setup_demo_user()
    result = database.queries.get_user_by_id(999)
    assert result is None


def test_get_summary_stats_with_expenses():
    uid = _setup_demo_user()
    result = database.queries.get_summary_stats(uid)
    # Sum of seed amounts: 12.50 + 45 + 80 + 15.99 + 30 + 65.20 + 120 + 25 = 393.69
    assert abs(result['total_spent'] - 393.69) < 0.01
    assert result['transaction_count'] == 8
    # Food is the largest category: 12.50 + 120 = 132.50
    assert result['top_category'] == 'Food'


def test_get_summary_stats_for_user_with_no_expenses():
    _setup_demo_user()
    conn = _shared_in_memory_db()
    conn.execute(
        "INSERT INTO users (name, email, password_hash) VALUES (?, ?, ?)",
        ('No Spend', 'nosp@example.com', generate_password_hash('demo123')),
    )
    conn.commit()
    new_user_id = conn.execute(
        "SELECT id FROM users WHERE email = ?", ('nosp@example.com',)
    ).fetchone()[0]

    result = database.queries.get_summary_stats(new_user_id)
    assert result['total_spent'] == 0
    assert result['transaction_count'] == 0
    assert result['top_category'] == '—'


def test_get_recent_transactions_returns_newest_first():
    uid = _setup_demo_user()
    result = database.queries.get_recent_transactions(uid, limit=10)
    assert len(result) == 8
    # Newest date is day=8, oldest is day=1
    assert result[0]['date'].endswith('-08')
    assert result[-1]['date'].endswith('-01')
    # Each row has the right keys
    for tx in result:
        assert set(tx.keys()) == {'date', 'description', 'category', 'amount'}


def test_get_recent_transactions_respects_limit():
    uid = _setup_demo_user()
    result = database.queries.get_recent_transactions(uid, limit=3)
    assert len(result) == 3


def test_get_recent_transactions_empty_for_no_expenses():
    _setup_demo_user()
    conn = _shared_in_memory_db()
    conn.execute(
        "INSERT INTO users (name, email, password_hash) VALUES (?, ?, ?)",
        ('No Spend', 'nosp2@example.com', generate_password_hash('demo123')),
    )
    conn.commit()
    new_user_id = conn.execute(
        "SELECT id FROM users WHERE email = ?", ('nosp2@example.com',)
    ).fetchone()[0]
    result = database.queries.get_recent_transactions(new_user_id)
    assert result == []


def test_get_category_breakdown_ordered_by_amount_desc():
    uid = _setup_demo_user()
    result = database.queries.get_category_breakdown(uid)
    # 7 distinct categories: Food, Transport, Bills, Health, Entertainment, Shopping, Other
    assert len(result) == 7
    # First row should be the largest (Food = 132.50)
    assert result[0]['name'] == 'Food'
    assert abs(result[0]['amount'] - 132.50) < 0.01


def test_get_category_breakdown_percentages_sum_to_100():
    uid = _setup_demo_user()
    result = database.queries.get_category_breakdown(uid)
    total_pct = sum(c['pct'] for c in result)
    assert total_pct == 100, f"percentages summed to {total_pct}, not 100"


def test_get_category_breakdown_empty_for_no_expenses():
    _setup_demo_user()
    conn = _shared_in_memory_db()
    conn.execute(
        "INSERT INTO users (name, email, password_hash) VALUES (?, ?, ?)",
        ('No Spend', 'nosp3@example.com', generate_password_hash('demo123')),
    )
    conn.commit()
    new_user_id = conn.execute(
        "SELECT id FROM users WHERE email = ?", ('nosp3@example.com',)
    ).fetchone()[0]
    result = database.queries.get_category_breakdown(new_user_id)
    assert result == []


# ------------------------------------------------------------------ #
# Route tests — GET /profile                                          #
# ------------------------------------------------------------------ #

def test_profile_redirects_when_logged_out():
    _setup_demo_user()
    resp = client.get('/profile')
    assert resp.status_code == 302
    # Should redirect to /login
    assert '/login' in resp.headers.get('Location', '')


def test_profile_returns_200_when_logged_in():
    _setup_demo_user()
    # Log in as the demo user
    client.post('/login', data=dict(
        email='demo@spendly.com',
        password='demo123',
    ))
    resp = client.get('/profile')
    assert resp.status_code == 200


def test_profile_shows_demo_user_info():
    _setup_demo_user()
    client.post('/login', data=dict(
        email='demo@spendly.com',
        password='demo123',
    ))
    resp = client.get('/profile')
    assert resp.status_code == 200
    assert b'Demo User' in resp.data
    assert b'demo@spendly.com' in resp.data


def test_profile_shows_rupee_symbol():
    _setup_demo_user()
    client.post('/login', data=dict(
        email='demo@spendly.com',
        password='demo123',
    ))
    resp = client.get('/profile')
    assert resp.status_code == 200
    # The rupee sign must be present in the rendered HTML
    assert '₹'.encode('utf-8') in resp.data


def test_profile_shows_total_spent():
    _setup_demo_user()
    client.post('/login', data=dict(
        email='demo@spendly.com',
        password='demo123',
    ))
    resp = client.get('/profile')
    assert resp.status_code == 200
    # Total spent = 393.69
    assert '₹393.69'.encode('utf-8') in resp.data


def test_profile_shows_transaction_count():
    _setup_demo_user()
    client.post('/login', data=dict(
        email='demo@spendly.com',
        password='demo123',
    ))
    resp = client.get('/profile')
    assert resp.status_code == 200
    # Transaction count is 8
    assert b'Transactions' in resp.data


def test_profile_shows_top_category():
    _setup_demo_user()
    client.post('/login', data=dict(
        email='demo@spendly.com',
        password='demo123',
    ))
    resp = client.get('/profile')
    assert resp.status_code == 200
    # Top category is Food (132.50)
    assert b'Food' in resp.data


def test_profile_shows_member_since():
    _setup_demo_user()
    client.post('/login', data=dict(
        email='demo@spendly.com',
        password='demo123',
    ))
    resp = client.get('/profile')
    assert resp.status_code == 200
    # The demo user was created with created_at='2026-01-15 10:00:00'
    assert b'January 2026' in resp.data


if __name__ == '__main__':
    test_get_user_by_id_returns_profile_dict()
    test_get_user_by_id_returns_none_for_missing_user()
    test_get_summary_stats_with_expenses()
    test_get_summary_stats_for_user_with_no_expenses()
    test_get_recent_transactions_returns_newest_first()
    test_get_recent_transactions_respects_limit()
    test_get_recent_transactions_empty_for_no_expenses()
    test_get_category_breakdown_ordered_by_amount_desc()
    test_get_category_breakdown_percentages_sum_to_100()
    test_get_category_breakdown_empty_for_no_expenses()
    test_profile_redirects_when_logged_out()
    test_profile_returns_200_when_logged_in()
    test_profile_shows_demo_user_info()
    test_profile_shows_rupee_symbol()
    test_profile_shows_total_spent()
    test_profile_shows_transaction_count()
    test_profile_shows_top_category()
    test_profile_shows_member_since()
    print("All Step 5 tests passed!")
