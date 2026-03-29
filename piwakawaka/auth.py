import re
import bcrypt
from functools import wraps
from flask import render_template, request, redirect, url_for, session, flash
from piwakawaka import app
from piwakawaka import db


def login_required(f):
    """
    Decorator that ensures a user is authenticated and authorised to access a route.

    This decorator performs the following checks:
    1. Verifies that the user is logged in (session contains user_id)
    2. Retrieves the latest account status and role from the database
    3. Prevents access if the account is inactive
    4. Synchronises the session role with the database (for role updates)
    5. Handles edge cases where the user record no longer exists

    If any check fails, the user is redirected to the login page with an appropriate message.

    This ensures:
    - Inactive users cannot access the system
    - Role changes take effect immediately without re-login
    - Sessions remain consistent with the database state

    :param f: The view function being decorated
    :return: Wrapped function with authentication and authorisation checks
    """    
    @wraps(f)
    def decorated(*args, **kwargs):

        # Step 1: Check whether the user is logged in
        # If there is no user_id stored in the session, redirect to login page
        if not session.get('user_id'):
            flash('Please log in to access this page.', 'warning')
            return redirect(url_for('login'))

        # Step 2: Retrieve the latest user status and role from the database
        # This ensures that any changes made by an Admin are immediately enforced
        cursor = db.get_cursor()
        cursor.execute("""
            SELECT
                u.is_active,
                r.name AS role_name
            FROM "user" u
            JOIN role r ON u.role_id = r.id
            WHERE u.id = %s;
        """, (session['user_id'],))
        user = cursor.fetchone()
        cursor.close()

        # Step 3: Handle edge case where the user no longer exists
        # This could happen if the account was deleted
        if not user:
            session.clear()
            flash('User account not found. Please log in again.', 'danger')
            return redirect(url_for('login'))

        # Step 4: Check if the account is inactive
        # If inactive, terminate the session and force logout
        if not user['is_active']:
            session.clear()
            flash('Your account has been deactivated. Please contact the system administrator.', 'danger')
            return redirect(url_for('login'))

        # Step 5: Synchronize the user's role with the latest value in the database
        # This ensures role changes take effect without requiring re-login
        session['role'] = user['role_name']

        # Step 6: Allow access to the requested view
        return f(*args, **kwargs)

    return decorated

def role_required(*roles):
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            if session.get('role') not in roles:
                flash('You do not have permission to access this page.', 'danger')
                return redirect(url_for('dashboard'))
            return f(*args, **kwargs)
        return decorated
    return decorator


def validate_password(password):
    """Return an error message string, or None if the password is valid."""
    if len(password) < 8:
        return 'Password must be at least 8 characters long.'
    if not re.search(r'[A-Z]', password):
        return 'Password must contain at least one uppercase letter.'
    if not re.search(r'[a-z]', password):
        return 'Password must contain at least one lowercase letter.'
    if not re.search(r'\d', password):
        return 'Password must contain at least one number.'
    return None


@app.route('/register', methods=['GET', 'POST'])
def register():
    if session.get('user_id'):
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        first_name = request.form.get('first_name', '').strip()
        last_name = request.form.get('last_name', '').strip()
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip()
        phone = request.form.get('phone', '').strip() or None
        emergency_contact_name = request.form.get('emergency_contact_name', '').strip() or None
        emergency_contact_phone = request.form.get('emergency_contact_phone', '').strip() or None
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')

        form_data = {
            'first_name': first_name,
            'last_name': last_name,
            'username': username,
            'email': email,
            'phone': phone or '',
            'emergency_contact_name': emergency_contact_name or '',
            'emergency_contact_phone': emergency_contact_phone or '',
        }

        errors = {}
        if not first_name:
            errors['first_name'] = 'First name is required.'
        elif len(first_name) <= 2:
            errors['first_name'] = 'Must be more than 2 characters.'
        elif first_name[0].isdigit():
            errors['first_name'] = 'Must not start with a number.'
        if not last_name:
            errors['last_name'] = 'Last name is required.'
        elif len(last_name) <= 2:
            errors['last_name'] = 'Must be more than 2 characters.'
        elif last_name[0].isdigit():
            errors['last_name'] = 'Must not start with a number.'
        if not username:
            errors['username'] = 'Username is required.'
        elif len(username) < 3:
            errors['username'] = 'Username must be at least 3 characters.'
        elif not re.match(r'^[A-Za-z0-9_]+$', username):
            errors['username'] = 'Username may only contain letters, numbers, and underscores.'
        if not email:
            errors['email'] = 'Email is required.'
        elif not re.match(r'^[^@\s]+@[^@\s]+\.[^@\s]+$', email):
            errors['email'] = 'Please enter a valid email address.'
        if not password:
            errors['password'] = 'Password is required.'
        elif validate_password(password):
            errors['password'] = validate_password(password)
        if not confirm_password:
            errors['confirm_password'] = 'Please confirm your password.'
        elif password and password != confirm_password:
            errors['confirm_password'] = 'Passwords do not match.'
        if phone and not re.match(r'^\+?[\d\s\-\(\)]{7,20}$', phone):
            errors['phone'] = 'Please enter a valid phone number (e.g. 021 123 4567 or +64 21 123 4567).'
        if emergency_contact_phone and not re.match(r'^\+?[\d\s\-\(\)]{7,20}$', emergency_contact_phone):
            errors['emergency_contact_phone'] = 'Please enter a valid phone number.'

        if errors:
            return render_template('register.html', form_data=form_data, errors=errors)

        password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

        try:
            cursor = db.get_cursor()

            cursor.execute('SELECT id FROM "user" WHERE username = %s', (username,))
            if cursor.fetchone():
                errors['username'] = 'Username already taken.'
                cursor.close()
                return render_template('register.html', form_data=form_data, errors=errors)

            cursor.execute('SELECT id FROM "user" WHERE email = %s', (email,))
            if cursor.fetchone():
                errors['email'] = 'An account with this email already exists.'
                cursor.close()
                return render_template('register.html', form_data=form_data, errors=errors)

            cursor.execute("SELECT id FROM role WHERE name = 'Observer'")
            role_row = cursor.fetchone()
            if not role_row:
                flash('System error: Observer role not found. Please contact an administrator.', 'danger')
                cursor.close()
                return render_template('register.html', form_data=form_data, errors={})

            cursor.execute(
                '''INSERT INTO "user"
                   (username, email, password_hash, first_name, last_name,
                    phone, emergency_contact_name, emergency_contact_phone, role_id)
                   VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)''',
                (username, email, password_hash, first_name, last_name,
                 phone, emergency_contact_name, emergency_contact_phone, role_row['id'])
            )
            db.get_db().commit()
            cursor.close()

            flash('Registration successful! Please log in.', 'success')
            return redirect(url_for('login'))

        except Exception as e:
            flash('A database error occurred. Please try again later.', 'danger')
            app.logger.error(f'Registration error: {e}')
            return render_template('register.html', form_data=form_data, errors={})

    return render_template('register.html', form_data={}, errors={})


@app.route('/login', methods=['GET', 'POST'])
def login():
    if session.get('user_id'):
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')

        if not username or not password:
            flash('Please enter your username and password.', 'danger')
            return render_template('login.html', username=username)

        try:
            cursor = db.get_cursor()
            cursor.execute(
                '''SELECT u.id, u.username, u.password_hash, u.is_active, r.name AS role
                   FROM "user" u
                   JOIN role r ON u.role_id = r.id
                   WHERE u.username = %s''',
                (username,)
            )
            user = cursor.fetchone()
            cursor.close()

            if user and bcrypt.checkpw(password.encode('utf-8'), user['password_hash'].encode('utf-8')):
                # Block inactive accounts
                if not user['is_active']:
                    flash('Your account has been deactivated. Please contact an administrator.', 'danger')
                    return render_template('login.html', username=username)

                session['user_id'] = user['id']
                session['username'] = user['username']
                session['role'] = user['role']
                return redirect(url_for('dashboard'))
            else:
                flash('Invalid username or password.', 'danger')
                return render_template('login.html', username=username)

        except Exception as e:
            flash('A database error occurred. Please try again later.', 'danger')
            app.logger.error(f'Login error: {e}')
            return render_template('login.html', username=username)

    return render_template('login.html')


@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out.', 'success')
    return redirect(url_for('home'))
