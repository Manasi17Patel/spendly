#!/usr/bin/env python3
"""
Seed a user into the database if one doesn't exist.
Accepts optional --email, --name, and --password arguments.
"""
import argparse
import os
import sys

# Add the project root to the path so we can import from database
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database.db import get_db, generate_password_hash

def seed_user(email=None, name=None, password=None):
    """Seed a user into the database if one doesn't exist."""
    # Set default values if not provided
    if email is None:
        email = 'demo@spendly.com'
    if name is None:
        name = 'Demo User'
    if password is None:
        password = 'demo123'

    conn = get_db()
    try:
        # Check if a user with this email already exists
        cursor = conn.execute("SELECT id FROM users WHERE email = ?", (email,))
        existing_user = cursor.fetchone()

        if existing_user:
            print(f"User with email '{email}' already exists (ID: {existing_user['id']})")
            return existing_user['id']

        # Create the user
        password_hash = generate_password_hash(password)
        cursor = conn.execute('''
            INSERT INTO users (name, email, password_hash)
            VALUES (?, ?, ?)
        ''', (name, email, password_hash))
        user_id = cursor.lastrowid
        conn.commit()

        print(f"Created user '{name}' with email '{email}' (ID: {user_id})")

        # Optionally add sample expenses.

        return user_id

    except Exception as e:
        print(f"Error seeding user: {e}")
        return None
    finally:
        conn.close()

def main():
    parser = argparse.ArgumentParser(description='Seed a user into the database')
    parser.add_argument('--email', type=str, help='Email address for the user')
    parser.add_argument('--name', type=str, help='Name for the user')
    parser.add_argument('--password', type=str, help='Password for the user')

    args = parser.parse_args()

    user_id = seed_user(email=args.email, name=args.name, password=args.password)

    if user_id is not None:
        print(f"Successfully seeded user with ID: {user_id}")
        return 0
    else:
        print("Failed to seed user")
        return 1

if __name__ == '__main__':
    sys.exit(main())