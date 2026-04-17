# US6  Create Lines (Admin)
# US7  Add Traps (Admin) - Carter
# US8  Edit Lines & Traps (Admin)
# US9  Retire Lines & Traps (Admin)
# US10 View Lines & Traps -

from flask import render_template, request, redirect, url_for, flash, session
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

def _fetch_lines_for_operator(cursor, operator_id):
    """Return lines assigned to the operator ordered by name."""
    cursor.execute("""
        SELECT
            l.id,
            l.name,
            l.line_type,
            l.is_retired
        FROM operator_line ol
        JOIN line l ON ol.line_id = l.id
        WHERE ol.operator_id = %s
        ORDER BY l.name;
    """, (operator_id,))
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

        if not errors:
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
    cursor = db.get_cursor()
    active_tab = request.args.get('tab', 'all')

    # Always fetch all lines for the "All Lines" tab
    all_lines = _fetch_lines_for_management(cursor)
    my_lines = _fetch_lines_for_operator(cursor, session.get('user_id')) if session.get('role') == 'Operator' else []

    cursor.close()

    return render_template(
        'lines/view_lines.html',
        all_lines=all_lines,
        my_lines=my_lines,
        active_tab=active_tab
    )

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

    trap_query = """
        SELECT
            id,
            code,
            trap_type,
            latitude,
            longitude,
            is_retired
        FROM trap
        WHERE line_id = %s
    """
    trap_params = [line_id]

    if session.get('role') != 'Admin':
        trap_query += " AND is_retired = FALSE"

    trap_query += " ORDER BY code;"

    cursor.execute(trap_query, trap_params)
    traps = cursor.fetchall()

    can_add_catch = False
    if not line['is_retired']:
        if session.get('role') == 'Admin':
            can_add_catch = True
        elif session.get('role') == 'Operator':
            cursor.execute("""
                SELECT 1
                FROM operator_line
                WHERE operator_id = %s AND line_id = %s;
            """, (session.get('user_id'), line_id))
            can_add_catch = cursor.fetchone() is not None

    cursor.close()

    return render_template(
        'lines/view_line_traps.html',
        line=line,
        traps=traps,
        can_add_catch=can_add_catch
    )


@app.route('/admin/lines/<int:line_id>/edit', methods=['GET', 'POST'])
@login_required
@role_required('Admin')
def edit_line(line_id):
    """
    Allow an Admin to edit an existing line.
    """
    cursor = db.get_cursor()

    cursor.execute("""
        SELECT id, name, line_type, is_retired
        FROM line
        WHERE id = %s;
    """, (line_id,))
    line = cursor.fetchone()

    if not line:
        cursor.close()
        flash('The selected line does not exist.', 'danger')
        return redirect(url_for('manage_lines'))

    form_data = {
        'name': line['name'],
        'line_type': line['line_type']
    }
    errors = {}

    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        line_type = request.form.get('line_type', '').strip()

        form_data = {'name': name, 'line_type': line_type}

        if not name:
            errors['name'] = 'Line name is required.'
        if not line_type:
            errors['line_type'] = 'Line type is required.'

        if line_type and line_type not in LINE_TYPES:
            errors['line_type'] = 'Invalid line type selected.'

        if name:
            cursor.execute("""
                SELECT id
                FROM line
                WHERE LOWER(name) = LOWER(%s) AND id <> %s;
            """, (name, line_id))
            existing_line = cursor.fetchone()
            if existing_line:
                errors['name'] = 'Line name is already taken.'

        if not errors:
            cursor.execute("""
                UPDATE line
                SET name = %s,
                    line_type = %s
                WHERE id = %s;
            """, (name, line_type, line_id))
            db.get_db().commit()
            cursor.close()

            flash('Line updated successfully.', 'success')
            return redirect(url_for('manage_lines'))

    cursor.close()
    return render_template(
        'lines/edit_line.html',
        line=line,
        line_types=LINE_TYPES,
        form_data=form_data,
        errors=errors
    )


@app.route('/admin/traps/<int:trap_id>/edit', methods=['GET', 'POST'])
@login_required
@role_required('Admin')
def edit_trap(trap_id):
    """
    Allow an Admin to edit an existing trap.
    """
    cursor = db.get_cursor()

    cursor.execute("""
        SELECT id, code, trap_type, line_id, latitude, longitude, is_retired
        FROM trap
        WHERE id = %s;
    """, (trap_id,))
    trap = cursor.fetchone()

    if not trap:
        cursor.close()
        flash('The selected trap does not exist.', 'danger')
        return redirect(url_for('view_lines'))

    form_data = {
        'code': trap['code'],
        'trap_type': trap['trap_type'],
        'latitude': str(trap['latitude']),
        'longitude': str(trap['longitude'])
    }
    errors = {}

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

        if not code:
            errors['code'] = 'Trap code is required.'
        if not trap_type:
            errors['trap_type'] = 'Trap type is required.'
        if not latitude:
            errors['latitude'] = 'Latitude is required.'
        if not longitude:
            errors['longitude'] = 'Longitude is required.'

        if trap_type and trap_type not in TRAP_TYPES:
            errors['trap_type'] = 'Invalid trap type selected.'

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

        if code:
            cursor.execute("""
                SELECT id
                FROM trap
                WHERE LOWER(code) = LOWER(%s) AND id <> %s;
            """, (code, trap_id))
            existing_trap = cursor.fetchone()
            if existing_trap:
                errors['code'] = 'Trap code is already in use.'

        if not errors:
            cursor.execute("""
                UPDATE trap
                SET code = %s,
                    trap_type = %s,
                    latitude = %s,
                    longitude = %s
                WHERE id = %s;
            """, (code, trap_type, lat_value, lng_value, trap_id))
            db.get_db().commit()
            cursor.close()

            flash('Trap updated successfully.', 'success')
            return redirect(url_for('view_line_traps', line_id=trap['line_id']))

    cursor.close()
    return render_template(
        'lines/edit_trap.html',
        trap=trap,
        trap_types=TRAP_TYPES,
        form_data=form_data,
        errors=errors
    )


@app.route('/admin/lines/<int:line_id>/retire', methods=['POST'])
@login_required
@role_required('Admin')
def retire_line(line_id):
    """
    Retire a line so it no longer appears in the active list.

    Retiring a line also retires all traps on that line so Operators
    will not see them as active traps.
    """
    cursor = db.get_cursor()

    cursor.execute("""
        SELECT id, name, is_retired
        FROM line
        WHERE id = %s;
    """, (line_id,))
    line = cursor.fetchone()

    if not line:
        cursor.close()
        flash('The selected line does not exist.', 'danger')
        return redirect(url_for('manage_lines'))

    if line['is_retired']:
        cursor.close()
        flash('This line is already inactive.', 'warning')
        return redirect(url_for('manage_lines'))

    cursor.execute("""
        UPDATE line
        SET is_retired = TRUE
        WHERE id = %s;
    """, (line_id,))

    cursor.execute("""
        UPDATE trap
        SET is_retired = TRUE
        WHERE line_id = %s;
    """, (line_id,))

    db.get_db().commit()
    cursor.close()

    flash('Line retired successfully.', 'success')
    return redirect(url_for('manage_lines'))


@app.route('/admin/traps/<int:trap_id>/retire', methods=['POST'])
@login_required
@role_required('Admin')
def retire_trap(trap_id):
    """
    Retire an individual trap so it no longer appears in the active list.
    """
    cursor = db.get_cursor()

    cursor.execute("""
        SELECT id, code, line_id, is_retired
        FROM trap
        WHERE id = %s;
    """, (trap_id,))
    trap = cursor.fetchone()

    if not trap:
        cursor.close()
        flash('The selected trap does not exist.', 'danger')
        return redirect(url_for('view_lines'))

    if trap['is_retired']:
        cursor.close()
        flash('This trap is already inactive.', 'warning')
        return redirect(url_for('view_line_traps', line_id=trap['line_id']))

    cursor.execute("""
        UPDATE trap
        SET is_retired = TRUE
        WHERE id = %s;
    """, (trap_id,))

    db.get_db().commit()
    cursor.close()

    flash(f"Trap {trap['code']} retired successfully.", 'success')
    return redirect(url_for('view_line_traps', line_id=trap['line_id']))


@app.route('/admin/lines/<int:line_id>/restore', methods=['POST'])
@login_required
@role_required('Admin')
def restore_line(line_id):
    """
    Restore a retired line back to active status.

    Restoring a line also restores all traps on that line.
    """
    cursor = db.get_cursor()

    cursor.execute("""
        SELECT id, name, is_retired
        FROM line
        WHERE id = %s;
    """, (line_id,))
    line = cursor.fetchone()

    if not line:
        cursor.close()
        flash('The selected line does not exist.', 'danger')
        return redirect(url_for('manage_lines'))

    if not line['is_retired']:
        cursor.close()
        flash('This line is already active.', 'warning')
        return redirect(url_for('manage_lines'))

    cursor.execute("""
        UPDATE line
        SET is_retired = FALSE
        WHERE id = %s;
    """, (line_id,))

    cursor.execute("""
        UPDATE trap
        SET is_retired = FALSE
        WHERE line_id = %s;
    """, (line_id,))

    db.get_db().commit()
    cursor.close()

    flash('Line restored successfully.', 'success')
    return redirect(url_for('manage_lines'))


@app.route('/admin/traps/<int:trap_id>/restore', methods=['POST'])
@login_required
@role_required('Admin')
def restore_trap(trap_id):
    """
    Restore a retired trap back to active status.
    """
    cursor = db.get_cursor()

    cursor.execute("""
        SELECT id, code, line_id, is_retired
        FROM trap
        WHERE id = %s;
    """, (trap_id,))
    trap = cursor.fetchone()

    if not trap:
        cursor.close()
        flash('The selected trap does not exist.', 'danger')
        return redirect(url_for('view_lines'))

    if not trap['is_retired']:
        cursor.close()
        flash('This trap is already active.', 'warning')
        return redirect(url_for('view_line_traps', line_id=trap['line_id']))

    cursor.execute("""
        UPDATE trap
        SET is_retired = FALSE
        WHERE id = %s;
    """, (trap_id,))

    db.get_db().commit()
    cursor.close()

    flash(f"Trap {trap['code']} restored successfully.", 'success')
    return redirect(url_for('view_line_traps', line_id=trap['line_id']))


@app.route('/line-assignments')
@login_required
def view_line_assignments():
    """
    US11: View line assignments.
    - Operator: sees only their own assigned lines (read-only)
    - Admin: redirected to manage_line_assignments
    - Observer: access denied
    """
    role = session.get('role')

    if role == 'Admin':
        return redirect(url_for('manage_line_assignments'))

    if role != 'Operator':
        flash('Access denied.', 'danger')
        return redirect(url_for('home'))

    user_id = session.get('user_id')
    cursor = db.get_cursor()

    cursor.execute("""
        SELECT
            l.id,
            l.name,
            l.line_type,
            l.is_retired,
            ol.assignment_date
        FROM operator_line ol
        JOIN line l ON ol.line_id = l.id
        WHERE ol.operator_id = %s
        ORDER BY l.name;
    """, (user_id,))

    assigned_lines = cursor.fetchall()
    cursor.close()

    return render_template(
        'lines/view_line_assignments.html',
        assigned_lines=assigned_lines
    )
