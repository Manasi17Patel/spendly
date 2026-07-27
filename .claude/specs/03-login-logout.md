# Spec: Login and Logout

## Overview
This step implements user authentication for Spendly, allowing registered users to log in and log out of the application. It builds upon the user registration feature (Step 2) by adding credential verification and session management. Users can submit their email and password via the login form; upon successful validation, a session is established and they are redirected to their profile page (or a placeholder). Logging out clears the session and redirects to the landing page. This feature is essential for providing personalized experiences and securing user data.

## Depends on
- Step 1: Database setup (users table exists with email and password_hash)
- Step 2: User registration (users can create accounts)

## Routes
- `POST /login` — Process login form submission; validates credentials, sets user session, redirects to profile page (or placeholder) — accessible to unauthenticated users (public)
- `GET /logout` — Clear user session and redirect to landing page — requires authentication (user must be logged in)

Note: The existing `GET /login` route (renders login.html) remains unchanged.

## Database changes
No schema changes are required. However, the following function will be added to `database/db.py`:
- `get_user_by_email(email)`: Retrieve a user record by email address.
- `verify_password(stored_hash, provided_password)`: Verify a plain-text password against a stored hash using `werkzeug.security.check_password_hash`.
These functions will be used by the login route to authenticate users.

## Templates
- **Modify:** `templates/login.html`
  - Add logic to retain the email input value after a failed login attempt (similar to registration form).
  - Ensure error messages are displayed via the existing `{{ error }}` variable (already present in the template).
  - Optionally add a success flash message upon successful login (though login will redirect, so message may be shown on the destination page).

## Files to change
- `app.py` – Add `login_post` route and `logout` route; import `session` and `flash` from Flask; import new authentication helpers from `database.db`.
- `database/db.py` – Add `get_user_by_email` and `verify_password` functions (or incorporate verification into a single `authenticate_user` function).
- `templates/login.html` – Modify to preserve email input on failed login.

## Files to create
None (no new templates or static files required for this step).

## New dependencies
No new dependencies. The required `werkzeug.security` module is already installed via `Flask` (as seen in `database/db.py`).

## Rules for implementation
- No SQLAlchemy or ORMs; use only the `sqlite3` module via the existing `get_db()` connection.
- Use parameterised queries (placeholders `?`) for all SQL statements to prevent SQL injection.
- Passwords must be hashed using `werkzeug.security.generate_password_hash` (already used in `create_user`) and verified with `check_password_hash`.
- Use Flask's `session` to store user ID upon login; clear session on logout.
- All templates must extend `base.html` (already the case).
- Use CSS variables for styling; avoid hardcoding hex values in CSS (existing stylesheet already complies).
- Follow the existing pattern for flash messages: use `flash(message, category)` with categories `"error"` and `"success"`.
- Implement POST/Redirect/Get pattern: after successful login, redirect to a GET endpoint to avoid form resubmission.

## Definition of done
- [ ] Users can access the login form at `/login` (GET) and see the form with fields for email and password.
- [ ] Submitting the login form with valid credentials (email and password of an existing user) logs the user in, sets a session, and redirects to `/profile` (or a placeholder page if profile is not yet implemented).
- [ ] Submitting the login form with invalid credentials (non-existent email or incorrect password) re-renders the login form with an error message and retains the entered email address.
- [ ] After logging in, visiting `/logout` clears the session and redirects the user to the landing page (`/`).
- [ ] Accessing `/logout` while not logged in redirects to the landing page without error.
- [ ] Passwords are never stored in plain text; only hashes are saved in the database.
- [ ] All database interactions use parameterised queries.
- [ ] No new pip packages are required; the implementation works with the existing `requirements.txt`.
- [ ] The existing `login.html` template is modified only to retain the email input on failure; no other changes are required.