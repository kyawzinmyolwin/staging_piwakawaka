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

LINE_TYPES = ['Trap']

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

def _fetch_lines_for_management(cursor):
    """Return all lines ordered by name for line management pages."""
    cursor.execute("""
        SELECT
            id,
            name,
            line_type,
            is_retired
        FROM line
        ORDER BY name;
    """)
    return cursor.fetchall()


@app.route('/admin/lines', methods=['GET', 'POST'])
@login_required
@role_required('Admin')
def manage_lines():
    """
    Create and view trap lines.

    User Story support:
    - Admin can create a line with valid name and type
    - duplicate names are rejected
    - missing required fields are rejected
    - success/error feedback is shown to the user
    """
    cursor = db.get_cursor()

    errors = {}
    form_data = {'name': '', 'line_type': ''}

    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        line_type = request.form.get('line_type', '').strip()

        form_data = {'name': name, 'line_type': line_type}

        # Required field validation
        if not name:
            errors['name'] = 'Line name is required.'
        if not line_type:
            errors['line_type'] = 'Line type is required.'

        # Allowed value validation
        if line_type and line_type not in LINE_TYPES:
            errors['line_type'] = 'Invalid line type selected.'

        # Duplicate validation (case-insensitive)
        if name:
            cursor.execute("""
                SELECT id
                FROM line
                WHERE LOWER(name) = LOWER(%s);
            """, (name,))
            existing_line = cursor.fetchone()
            if existing_line:
                errors['name'] = 'Line name is already taken.'

        if errors:
            flash('Unable to create line. Please fix the form errors.', 'danger')
        else:
            cursor.execute("""
                INSERT INTO line (name, line_type, is_retired)
                VALUES (%s, %s, FALSE);
            """, (name, line_type))
            db.get_db().commit()
            cursor.close()

            flash('Line created successfully.', 'success')
            return redirect(url_for('manage_lines'))

    lines = _fetch_lines_for_management(cursor)
    cursor.close()

    return render_template(
        'lines/manage_lines.html',
        lines=lines,
        line_types=LINE_TYPES,
        errors=errors,
        form_data=form_data
    )


@app.route('/lines')
@login_required
def view_lines():
    """
    View all lines for any authenticated role.

    User Story support:
    - Observer, Operator, and Admin can view all lines
    - line list includes active and inactive lines
    - list displays line name, type, and current status
    """
    cursor = db.get_cursor()
    lines = _fetch_lines_for_management(cursor)
    cursor.close()

    return render_template('lines/view_lines.html', lines=lines)


@app.route('/lines/<int:line_id>')
@login_required
def view_line_traps(line_id):
    """
    View all traps for a specific line for any authenticated role.

    User Story support:
    - clicking a line shows all traps on that line
    - if no traps exist, show a clear empty-state message
    """
    cursor = db.get_cursor()

    cursor.execute("""
        SELECT
            id,
            name,
            line_type,
            is_retired
        FROM line
        WHERE id = %s;
    """, (line_id,))
    line = cursor.fetchone()

    if not line:
        cursor.close()
        flash('The selected line does not exist.', 'danger')
        return redirect(url_for('view_lines'))

    cursor.execute("""
        SELECT
            code,
            trap_type,
            latitude,
            longitude,
            is_retired
        FROM trap
        WHERE line_id = %s
        ORDER BY code;
    """, (line_id,))
    traps = cursor.fetchall()
    cursor.close()

    return render_template('lines/view_line_traps.html', line=line, traps=traps)


# @app.route('/lines/<int:line_id>/traps/add', methods=['GET', 'POST'])
# @login_required
# @role_required('Admin')
# def add_trap_to_line(line_id):
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
