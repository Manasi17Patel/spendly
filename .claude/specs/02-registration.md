## 1. Overview

Implement user registration functionality for the Spendly application.

This step enables new users to create an account by providing their name, email, and password.
The password is securely hashed before storage. Upon successful registration, the user is
redirected to the login page.

This feature depends on the user table established in Step 1 (database setup).

## 2. Depends on

- Step 1: Database setup (users table must exist)

## 3. Routes

- **GET /register** (already implemented in app.py)  
  Renders the registration form (register.html).

- **POST /register** (to be implemented)  
  Processes the submitted registration form:
  - Validates input (presence, email format, password length)
  - Checks if email already exists
  - Hashes password using werkzeug.security.generate_password_hash
  - Inserts new user into the users table
  - On success: redirects to login page with a success message
  - On failure: re-renders the registration form with an error message

## 4. Database Schema

No changes to the schema are required. The existing `users` table (from Step 1) is used:

| Column | Type | Constraints |
|--------|------|-------------|
| id | INTEGER | Primary key, autoincrement |
| name | TEXT | Not null |
| email | TEXT | Unique, not null |
| password_hash | TEXT | Not null |
| created_at | TEXT | Default datetime('now') |

## 5. Functions to Implement (`database/db.py`)

### A. `create_user(name, email, password)`

- Parameters:
  - `name` (str): User's full name
  - `email` (str): User's email address (must be unique)
  - `password` (str): Plain-text password to be hashed
- Returns:
  - `int`: The newly created user's ID on success
  - `None`: If the email already exists
- Behavior:
  - Validates that email is not already in use (SELECT)
  - Hashes the password using `generate_password_hash`
  - Inserts the new user into the `users` table using a parameterized query
  - Returns the new user's ID (from `lastrowid`)
  - Rolls back the transaction on any error

## 6. Changes to `app.py`

- Import the new `create_user` function from `database.db`
- Add a route handler for `POST /register`:
  - Extract form data (name, email, password)
  - Call `create_user(name, email, password)`
  - If user is created successfully:
      - Flash a success message (e.g., "Account created! Please log in.")
      - Redirect to `/login`
  - If email already exists:
      - Flash an error message (e.g., "Email already registered.")
      - Re-render `register.html` with the error and previously entered name/email (to avoid retyping)
  - Handle any other validation errors (empty fields, invalid email, short password) similarly

## 7. Files to Change

- `database/db.py` → add `create_user` function
- `app.py` → add import and implement `POST /register` route

## 8. Files to Create

- None (the registration template `register.html` already exists)

## 9. Dependencies

- No new pip packages required
- Uses existing dependencies:
  - `flask` (for routing, request, redirect, flash, render_template)
  - `werkzeug.security` (for password hashing, already installed)

## 10. Rules for Implementation

- Use **parameterized queries only** — never use string formatting in SQL
- Hash passwords using `generate_password_hash` (do not store plain-text passwords)
- Validate input on the server side (do not rely solely on client-side validation)
- Ensure the email uniqueness constraint is enforced at the database level (UNIQUE index) and also checked in the application logic to provide a user-friendly error
- Use Flask's `flash` mechanism to display success/error messages
- Redirect after successful POST (Post/Redirect/Get pattern) to avoid form resubmission
- Do not change the existing GET `/register` route (it already renders the template)

## 11. Expected Behavior

- When a user visits `/register`, they see the registration form.
- Upon submitting the form with valid, unique data:
    - A new user is created in the database.
    - The user is redirected to `/login`.
    - A success message is displayed on the login page.
- Upon submitting the form with an email that already exists:
    - The form is re-rendered with an error message.
    - The previously entered name and email are preserved in the form fields.
- Upon submitting the form with missing or invalid data (e.g., short password):
    - The form is re-rendered with an appropriate error message.
- All database operations are performed within a transaction and are rolled back on error.
- The application never stores plain-text passwords.

## 12. Error Handling Expectations

- Duplicate email: caught via `SELECT` before insert (or via database integrity error) and results in a user-friendly error message.
- Database connection errors: should result in a generic error message (to avoid leaking details) and the form is re-rendered.
- Validation errors (missing fields, invalid email, password too short): caught and displayed before attempting database operations.

## 13. Definition of Done

- [ ]  Users can access the registration form at `/register` (GET)
- [ ]  Submitting the form with valid, unique data creates a new user account
- [ ]  Password is stored as a hash (not plain text) in the database
- [ ]  Duplicate email submissions are rejected with an error message
- [ ]  Form validation prevents submission with missing or invalid data
- [ ]  Successful registration redirects to `/login` with a success message
- [ ]  All database interactions use parameterized queries
- [ ]  No new pip packages are required
- [ ]  The existing `register.html` template is used without modification (except for displaying errors and preserving input values via Flask's form handling)