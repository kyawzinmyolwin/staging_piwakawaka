# US4 Change Password
# US5 View/Edit Own Profile
import bcrypt
from flask import render_template, request, redirect, url_for, flash, session
from piwakawaka import app, db
from piwakawaka.auth import login_required, validate_password


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
