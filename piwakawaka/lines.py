# US6  Create Lines (Admin)
# US7  Add Traps (Admin) - Carter
# US8  Edit Lines & Traps (Admin)
# US9  Retire Lines & Traps (Admin)
# US10 View Lines & Traps

from flask import render_template, request, redirect, url_for, flash
from decimal import Decimal, InvalidOperation
from piwakawaka import app, db
from piwakawaka.auth import login_required, role_required


# Allowed trap types based on the database check constraint
TRAP_TYPES = [
    'A24', 'DOC 150', 'DOC 200', 'DOC 250',
    'Flipping Timmy', 'Rat trap', 'T-Rex Rat Trap',
    'Trapinator', 'Victor'
]


@app.route('/lines/<int:line_id>/traps/add', methods=['GET', 'POST'])
@login_required
@role_required('Admin')
def add_trap_to_line(line_id):
    """
    Allow an Admin to add a new trap to a specific line.

    Validation rules:
    - the line must exist
    - the line must not be inactive/retired
    - trap code is required and must be unique
    - trap type is required and must be one of the allowed values
    - latitude and longitude are required and must be valid numbers
    """
    cursor = db.get_cursor()

    # Check that the selected line exists
    cursor.execute("""
        SELECT id, name, line_type, is_retired
        FROM line
        WHERE id = %s;
    """, (line_id,))
    line = cursor.fetchone()

    if not line:
        cursor.close()
        flash('The selected line does not exist.', 'danger')
        return redirect(url_for('view_lines'))

    if line['is_retired']:
        cursor.close()
        flash('Cannot add a trap to an inactive line.', 'danger')
        return redirect(url_for('view_lines'))

    errors = {}
    form_data = {}

    if request.method == 'POST':
        code = request.form.get('code', '').strip()
        trap_type = request.form.get('trap_type', '').strip()
        latitude = request.form.get('latitude', '').strip()
        longitude = request.form.get('longitude', '').strip()

        form_data = {
            'code': code,
            'trap_type': trap_type,
            'latitude': latitude,
            'longitude': longitude
        }

        # Required field validation
        if not code:
            errors['code'] = 'Trap code is required.'
        if not trap_type:
            errors['trap_type'] = 'Trap type is required.'
        if not latitude:
            errors['latitude'] = 'Latitude is required.'
        if not longitude:
            errors['longitude'] = 'Longitude is required.'

        # Trap type validation
        if trap_type and trap_type not in TRAP_TYPES:
            errors['trap_type'] = 'Invalid trap type selected.'

        # Coordinate validation
        lat_value = None
        lng_value = None

        if latitude:
            try:
                lat_value = Decimal(latitude)
            except InvalidOperation:
                errors['latitude'] = 'Latitude must be a valid number.'

        if longitude:
            try:
                lng_value = Decimal(longitude)
            except InvalidOperation:
                errors['longitude'] = 'Longitude must be a valid number.'

        if lat_value is not None and not (-90 <= lat_value <= 90):
            errors['latitude'] = 'Latitude must be between -90 and 90.'

        if lng_value is not None and not (-180 <= lng_value <= 180):
            errors['longitude'] = 'Longitude must be between -180 and 180.'

        # Unique trap code validation
        if code:
            cursor.execute("""
                SELECT id
                FROM trap
                WHERE LOWER(code) = LOWER(%s);
            """, (code,))
            existing_trap = cursor.fetchone()

            if existing_trap:
                errors['code'] = 'Trap code is already in use.'

        # If validation passes, insert the trap
        if not errors:
            cursor.execute("""
                INSERT INTO trap (code, trap_type, line_id, latitude, longitude, is_retired)
                VALUES (%s, %s, %s, %s, %s, FALSE);
            """, (code, trap_type, line_id, lat_value, lng_value))

            db.get_db().commit()
            cursor.close()

            flash('Trap added successfully.', 'success')
            return redirect(url_for('view_line_traps', line_id=line_id))

    cursor.close()
    return render_template(
        'admin/add_trap.html',
        line=line,
        trap_types=TRAP_TYPES,
        errors=errors,
        form_data=form_data
    )