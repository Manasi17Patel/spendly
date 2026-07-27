import os
# Set environment variable to prevent the app from initializing the database on import
os.environ['FLASK_ENV'] = 'testing'

import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from flask import Flask
from app import app
from database.db import get_db, init_db, seed_db, create_user

# Set up the app for testing
app.config['TESTING'] = True
app.config['SECRET_KEY'] = 'test-secret-key'  # Override for testing
client = app.test_client()

def test_login_logout():
    # Since we set FLASK_ENV to 'testing', the app did not run init_db and seed_db on import.
    # We need to initialize the database ourselves.
    with app.app_context():
        init_db()
        seed_db()  # This will seed the database with the demo user

    # Use the demo user that is seeded by seed_db()
    demo_email = 'demo@spendly.com'
    demo_password = 'demo123'

    # Test 1: Access login page (GET) when not logged in
    print("Testing GET /login (not logged in)")
    resp = client.get('/login')
    print(f"  Status: {resp.status_code}")
    print(f"  Data (first 200 bytes): {resp.data[:200]}")
    assert resp.status_code == 200
    assert b'Sign in' in resp.data

    # Test 2: Login with invalid credentials
    print("Testing POST /login with invalid credentials")
    resp = client.post('/login', data=dict(
        email='wrong@example.com',
        password='wrong'
    ))  # Do not follow redirects because we expect 400
    print(f"  Status: {resp.status_code}")
    print(f"  Data (first 200 bytes): {resp.data[:200]}")
    assert resp.status_code == 400
    assert b'Invalid' in resp.data  # Check for part of the error message
    # Also check that the email is retained in the form
    assert b'value="wrong@example.com"' in resp.data

    # Test 3: Login with valid credentials (demo user)
    print("Testing POST /login with valid credentials")
    resp = client.post('/login', data=dict(
        email=demo_email,
        password=demo_password
    ), follow_redirects=True)  # Follow redirects to see the final page
    print(f"  Status: {resp.status_code}")
    print(f"  Data (first 200 bytes): {resp.data[:200]}")
    assert resp.status_code == 200
    # Should redirect to landing page (now changed from profile to landing)
    assert b'Track every rupee' in resp.data
    # Check that the user is logged in by checking the session
    with client.session_transaction() as sess:
        print(f"  Session after login: {sess}")
        assert 'user_id' in sess

    # Test 4: Access logout route
    print("Testing GET /logout")
    resp = client.get('/logout', follow_redirects=True)
    print(f"  Status: {resp.status_code}")
    print(f"  Data (first 200 bytes): {resp.data[:200]}")
    assert resp.status_code == 200
    # Should redirect to landing page
    assert b'Track every rupee' in resp.data
    # Session should be cleared
    with client.session_transaction() as sess:
        print(f"  Session after logout: {sess}")
        assert 'user_id' not in sess

    # Test 5: Access login page when logged in (should redirect to landing)
    print("Testing GET /login (logged in) - should redirect to landing")
    # First, log in
    client.post('/login', data=dict(
        email=demo_email,
        password=demo_password
    ))
    # Now try to access login page
    resp = client.get('/login')
    print(f"  Status: {resp.status_code}")
    print(f"  Data (first 200 bytes): {resp.data[:200]}")
    assert resp.status_code == 302  # Redirect
    # Follow redirect to see final page
    resp = client.get('/login')  # This will follow redirect due to test client? Actually we need to follow manually or use follow_redirects=True
    # Let's do it with follow_redirects=True in the request
    resp = client.get('/login', follow_redirects=True)
    print(f"  After redirect status: {resp.status_code}")
    print(f"  After redirect data (first 200 bytes): {resp.data[:200]}")
    assert b'Track every rupee' in resp.data

    # Test 6: Access register page when logged in (should redirect to landing)
    print("Testing GET /register (logged in) - should redirect to landing")
    resp = client.get('/register', follow_redirects=True)
    print(f"  Status: {resp.status_code}")
    print(f"  Data (first 200 bytes): {resp.data[:200]}")
    assert resp.status_code == 200
    assert b'Track every rupee' in resp.data

    print("All tests passed!")

if __name__ == '__main__':
    test_login_logout()