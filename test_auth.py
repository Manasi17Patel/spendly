import os
import sys
import sqlite3
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from flask import Flask, session
from database.db import get_db, init_db, create_user
from werkzeug.security import generate_password_hash

# Override get_db to use an in-memory database for testing
def get_test_db():
    conn = sqlite3.connect(':memory:')
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn

# Monkey-patch the get_db function in the database.db module
import database.db
database.db.get_db = get_test_db

# Now import the app after patching
from app import app

# Set up the test client
app.config['TESTING'] = True
app.config['SECRET_KEY'] = 'test-secret-key'
client = app.test_client()

def test_login_logout():
    # Initialize the database and create a test user
    with app.app_context():
        init_db()
        # Create a test user (we'll use our own to avoid relying on seed data which might change)
        username = "testuser"
        email = "test@example.com"
        password = "testpassword123"  # must be at least 8 chars
        user_id = create_user(username, email, password)
        assert user_id is not None, "Failed to create test user"

    # Test 1: Access login page (GET)
    resp = client.get('/login')
    assert resp.status_code == 200
    assert b'Sign in' in resp.data  # Check for some text in the login form

    # Test 2: Login with invalid credentials
    resp = client.post('/login', data=dict(
        email='wrong@example.com',
        password='wrong'
    ), follow_redirects=True)
    assert resp.status_code == 200
    # Should show an error message
    assert b'Invalid' in resp.data  # Check for part of the error message

    # Test 3: Login with valid credentials
    resp = client.post('/login', data=dict(
        email=email,
        password=password
    ), follow_redirects=True)
    assert resp.status_code == 200
    # Should redirect to profile page (or wherever we set)
    # Check that we are redirected to the profile page by checking for a known string
    assert b'Profile page' in resp.data
    # Alternatively, check that the session has the user_id
    with client.session_transaction() as sess:
        assert 'user_id' in sess

    # Test 4: Access logout route
    resp = client.get('/logout', follow_redirects=True)
    assert resp.status_code == 200
    # Should redirect to landing page
    assert b'Welcome' in resp.data  # Landing page has "Welcome back" in the title
    # Session should be cleared
    with client.session_transaction() as sess:
        assert 'user_id' not in sess

    print("All tests passed!")

if __name__ == '__main__':
    test_login_logout()