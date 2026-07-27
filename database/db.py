import sqlite3
from werkzeug.security import generate_password_hash
import os
from datetime import date


def get_db():
    """Open a new database connection with foreign keys enabled and row factory."""
    # Database file is in the project root
    db_path = os.path.join(os.path.dirname(__file__), '..', 'spendly.db')
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    # Enable foreign key constraints
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    """Create tables if they don't exist."""
    conn = get_db()
    try:
        # Create users table
        conn.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                email TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        # Create expenses table
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
    finally:
        conn.close()


def seed_db():
    """Seed the database with demo data if empty."""
    conn = get_db()
    try:
        # Check if we already have users
        cursor = conn.execute("SELECT COUNT(*) FROM users")
        count = cursor.fetchone()[0]
        if count > 0:
            return  # Already seeded

        # Create demo user
        password_hash = generate_password_hash('demo123')
        cursor = conn.execute('''
            INSERT INTO users (name, email, password_hash)
            VALUES (?, ?, ?)
        ''', ('Demo User', 'demo@spendly.com', password_hash))
        user_id = cursor.lastrowid

        # Sample expenses data (8 expenses across all categories)
        categories = ['Food', 'Transport', 'Bills', 'Health', 'Entertainment', 'Shopping', 'Other']
        today = date.today()
        expenses_data = [
            (user_id, 12.50, 'Food', today.replace(day=1), 'Breakfast at cafe'),
            (user_id, 45.00, 'Transport', today.replace(day=2), 'Taxi to airport'),
            (user_id, 80.00, 'Bills', today.replace(day=3), 'Electricity bill'),
            (user_id, 15.99, 'Health', today.replace(day=4), 'Pharmacy'),
            (user_id, 30.00, 'Entertainment', today.replace(day=5), 'Movie tickets'),
            (user_id, 65.20, 'Shopping', today.replace(day=6), 'Groceries'),
            (user_id, 120.00, 'Food', today.replace(day=7), 'Weekend dinner'),
            (user_id, 25.00, 'Other', today.replace(day=8), 'Book purchase'),
        ]

        for expense in expenses_data:
            conn.execute('''
                INSERT INTO expenses (user_id, amount, category, date, description)
                VALUES (?, ?, ?, ?, ?)
            ''', expense)

        conn.commit()
    finally:
        conn.close()