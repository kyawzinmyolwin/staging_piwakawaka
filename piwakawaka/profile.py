# US4 Change Password
# US5 View/Edit Own Profile
import re
import bcrypt
from flask import render_template, request, redirect, url_for, flash, session
from piwakawaka import app, db
from piwakawaka.auth import login_required, validate_password


@app.route('/profile', methods=['GET', 'POST'])
@login_required
def view_profile():
    cursor = db.get_cursor()

    if request.method == 'POST':
        first_name = request.form.get('first_name', '').strip()
        last_name  = request.form.get('last_name', '').strip()
        email      = request.form.get('email', '').strip()
        phone                   = request.form.get('phone', '').strip() or None
        emergency_contact_name  = request.form.get('emergency_contact_name', '').strip() or None
        emergency_contact_phone = request.form.get('emergency_contact_phone', '').strip() or None

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

        if not email:
            errors['email'] = 'Email is required.'
        elif not re.match(r'^[^@\s]+@[^@\s]+\.[^@\s]+$', email):
            errors['email'] = 'Please enter a valid email address.'

        if phone and not re.match(r'^\+?[\d\s\-\(\)]{7,20}$', phone):
            errors['phone'] = 'Please enter a valid phone number.'

        if emergency_contact_phone and not re.match(r'^\+?[\d\s\-\(\)]{7,20}$', emergency_contact_phone):
            errors['emergency_contact_phone'] = 'Please enter a valid phone number.'

        if not errors:
            # Check email not taken by another user
            cursor.execute('SELECT id FROM "user" WHERE email = %s AND id != %s', (email, session['user_id']))
            if cursor.fetchone():
                errors['email'] = 'This email is already in use by another account.'

        if errors:
            # Re-fetch read-only fields to re-render page
            cursor.execute(
                'SELECT u.username, u.email, u.first_name, u.last_name, u.phone, '
                'u.emergency_contact_name, u.emergency_contact_phone, '
                'u.is_active, u.created_at, r.name AS role '
                'FROM "user" u JOIN role r ON u.role_id = r.id WHERE u.id = %s',
                (session['user_id'],)
            )
            user = cursor.fetchone()
            cursor.close()
            form_data = {
                'first_name': first_name, 'last_name': last_name, 'email': email,
                'phone': phone or '', 'emergency_contact_name': emergency_contact_name or '',
                'emergency_contact_phone': emergency_contact_phone or '',
            }
            return render_template('profile/view_profile.html', user=user, form_data=form_data, errors=errors)

        cursor.execute(
            'UPDATE "user" SET first_name=%s, last_name=%s, email=%s, '
            'phone=%s, emergency_contact_name=%s, emergency_contact_phone=%s '
            'WHERE id=%s',
            (first_name, last_name, email, phone,
             emergency_contact_name, emergency_contact_phone, session['user_id'])
        )
        db.get_db().commit()
        cursor.close()
        flash('Profile updated successfully.', 'success')
        return redirect(url_for('view_profile'))

    # GET
    cursor.execute(
        'SELECT u.username, u.email, u.first_name, u.last_name, u.phone, '
        'u.emergency_contact_name, u.emergency_contact_phone, '
        'u.is_active, u.created_at, r.name AS role '
        'FROM "user" u JOIN role r ON u.role_id = r.id WHERE u.id = %s',
        (session['user_id'],)
    )
    user = cursor.fetchone()
    cursor.close()
    return render_template('profile/view_profile.html', user=user, form_data=user, errors={})


@app.route('/profile/change-password', methods=['GET', 'POST'])
@login_required
def change_password():
    if request.method == 'POST':
        current_password = request.form.get('current_password', '')
        new_password = request.form.get('new_password', '')
        confirm_password = request.form.get('confirm_password', '')

        errors = {}

        if not current_password:
            errors['current_password'] = 'Current password is required.'
        if not new_password:
            errors['new_password'] = 'New password is required.'
        if not confirm_password:
            errors['confirm_password'] = 'Please confirm your new password.'

        if errors:
            return render_template('profile/change_password.html', errors=errors)

        cursor = db.get_cursor()
        cursor.execute('SELECT password_hash FROM "user" WHERE id = %s', (session['user_id'],))
        user = cursor.fetchone()
        cursor.close()

        if not bcrypt.checkpw(current_password.encode('utf-8'), user['password_hash'].encode('utf-8')):
            errors['current_password'] = 'Current password is incorrect.'
            return render_template('profile/change_password.html', errors=errors)

        if new_password == current_password:
            errors['new_password'] = 'New password must be different from your current password.'
            return render_template('profile/change_password.html', errors=errors)

        pw_error = validate_password(new_password)
        if pw_error:
            errors['new_password'] = pw_error
            return render_template('profile/change_password.html', errors=errors)

        if new_password != confirm_password:
            errors['confirm_password'] = 'Passwords do not match.'
            return render_template('profile/change_password.html', errors=errors)

        new_hash = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        cursor = db.get_cursor()
        cursor.execute('UPDATE "user" SET password_hash = %s WHERE id = %s', (new_hash, session['user_id']))
        db.get_db().commit()
        cursor.close()

        flash('Password changed successfully.', 'success')
        return redirect(url_for('dashboard'))

    return render_template('profile/change_password.html', errors={})
