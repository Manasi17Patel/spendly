import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import app

# Set up the test client
app.config['TESTING'] = True
app.config['SECRET_KEY'] = 'test-secret-key'
client = app.test_client()

def test_login_logout_with_demo_user():
    # Use the demo user that should already be in the database
    email = 'demo@spendly.com'
    password = 'demo123'

    # Test 1: Access login page (GET)
    resp = client.get('/login')
    print(f"GET /login: status={resp.status_code}, data={resp.data[:200]}")  # Debug
    assert resp.status_code == 200, f"Expected 200, got {resp.status_code}"
    assert b'Sign in' in resp.data, f"Expected 'Sign in' in response data: {resp.data[:200]}"

    # Test 2: Login with invalid credentials
    resp = client.post('/login', data=dict(
        email='wrong@example.com',
        password='wrong'
    ), follow_redirects=True)
    print(f"POST /login invalid: status={resp.status_code}, data={resp.data[:200]}")
    assert resp.status_code == 200, f"Expected 200, got {resp.status_code}"
    assert b'Invalid' in resp.data, f"Expected 'Invalid' in response data: {resp.data[:200]}"

    # Test 3: Login with valid credentials (demo user)
    resp = client.post('/login', data=dict(
        email=email,
        password=password
    ), follow_redirects=True)
    print(f"POST /login valid: status={resp.status_code}, data={resp.data[:200]}")
    assert resp.status_code == 200, f"Expected 200, got {resp.status_code}"
    # Should redirect to profile page
    assert b'Profile page' in resp.data, f"Expected 'Profile page' in response data: {resp.data[:200]"
    # Check that the user is logged in by checking the session
    with client.session_transaction() as sess:
        assert 'user_id' in sess, "User ID not found in session after login"

    # Test 4: Access logout route
    resp = client.get('/logout', follow_redirects=True)
    print(f"GET /logout: status={resp.status_code}, data={resp.data[:200]}")
    assert resp.status_code == 200, f"Expected 200, got {resp.status_code}"
    # Should redirect to landing page
    assert b'Welcome' in resp.data, f"Expected 'Welcome' in response data: {resp.data[:200]}"
    # Session should be cleared
    with client.session_transaction() as sess:
        assert 'user_id' not in sess, "User ID still in session after logout"

    print("All tests passed!")

if __name__ == '__main__':
    test_login_logout_with_demo_user()