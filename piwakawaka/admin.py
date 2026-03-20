# US11 View Operator-Line Assignments
# US12 Assign/Reassign Lines (Admin)
# US18 Manage Species (Admin)
# US19 Manage Trap Status (Admin)
# US20 Manage Bait Types (Admin)
# US22 View User List (Admin)
# US23 View User Profiles (Admin)
# US24 View Operator Activity (Admin)
# US25 Activate/Deactivate Accounts (Admin)
# US26 Change User Roles (Admin)
from flask import render_template, request, redirect, url_for, flash
from piwakawaka import app, db
from piwakawaka.auth import login_required, role_required


@app.route('/admin/line-assignments')
@login_required
@role_required('Admin')
def manage_line_assignments():
    """
    Display all lines and their current operator assignments.

    This page allows an Admin to:
    - view all lines
    - view the operators currently assigned to each line
    - assign an operator to a line
    - reassign a line from one operator to another
    """
    cursor = db.get_cursor()

    # Get all lines for display and assignment form
    cursor.execute("""
        SELECT
            l.id,
            l.name,
            l.line_type,
            l.is_retired
        FROM line l
        ORDER BY l.name;
    """)
    lines = cursor.fetchall()

    # Get all users with the Operator role
    cursor.execute("""
        SELECT
            u.id,
            u.first_name,
            u.last_name,
            u.username,
            u.is_active
        FROM "user" u
        JOIN role r ON u.role_id = r.id
        WHERE r.name = 'Operator'
        ORDER BY u.first_name, u.last_name, u.username;
    """)
    operators = cursor.fetchall()

    # Get all current assignments
    cursor.execute("""
        SELECT
            l.id AS line_id,
            l.name AS line_name,
            l.line_type,
            l.is_retired,
            u.id AS operator_id,
            u.first_name,
            u.last_name,
            u.username,
            u.is_active,
            ol.assignment_date
        FROM line l
        LEFT JOIN operator_line ol ON l.id = ol.line_id
        LEFT JOIN "user" u ON ol.operator_id = u.id
        LEFT JOIN role r ON u.role_id = r.id
        WHERE u.id IS NULL OR r.name = 'Operator'
        ORDER BY l.name, u.first_name, u.last_name;
    """)
    assignment_rows = cursor.fetchall()
    cursor.close()

    # Group assignments under each line for easier rendering
    grouped_lines = {}
    for line in lines:
        grouped_lines[line['id']] = {
            'line_id': line['id'],
            'line_name': line['name'],
            'line_type': line['line_type'],
            'is_retired': line['is_retired'],
            'operators': []
        }

    for row in assignment_rows:
        if row['operator_id'] is not None:
            grouped_lines[row['line_id']]['operators'].append({
                'operator_id': row['operator_id'],
                'full_name': f"{row['first_name']} {row['last_name']}",
                'username': row['username'],
                'is_active': row['is_active'],
                'assignment_date': row['assignment_date']
            })

    return render_template(
        'admin/manage_line_assignments.html',
        grouped_lines=grouped_lines,
        lines=lines,
        operators=operators,
        assign_errors={},
        assign_form={}
    )


@app.route('/admin/line-assignments/assign', methods=['POST'])
@login_required
@role_required('Admin')
def assign_line_to_operator():
    """
    Assign an operator to a line.

    Validation rules:
    - line must exist
    - operator must exist
    - line must not be inactive/retired
    - operator must be active
    - selected user must have the Operator role
    - duplicate assignments are not allowed
    """
    line_id = request.form.get('line_id', '').strip()
    operator_id = request.form.get('operator_id', '').strip()

    errors = {}

    # Validate raw input first
    if not line_id:
        errors['line_id'] = 'Please select a line.'
    if not operator_id:
        errors['operator_id'] = 'Please select an operator.'

    try:
        if line_id:
            line_id = int(line_id)
    except ValueError:
        errors['line_id'] = 'Invalid line selected.'

    try:
        if operator_id:
            operator_id = int(operator_id)
    except ValueError:
        errors['operator_id'] = 'Invalid operator selected.'

    cursor = db.get_cursor()

    selected_line = None
    selected_operator = None
    existing_assignment = None

    if not errors:
        # Check whether the selected line exists
        cursor.execute("""
            SELECT id, name, is_retired
            FROM line
            WHERE id = %s;
        """, (line_id,))
        selected_line = cursor.fetchone()

        # Check whether the selected operator exists and is really an Operator
        cursor.execute("""
            SELECT
                u.id,
                u.is_active,
                r.name AS role_name
            FROM "user" u
            JOIN role r ON u.role_id = r.id
            WHERE u.id = %s;
        """, (operator_id,))
        selected_operator = cursor.fetchone()

        # Check duplicate assignment using the composite key
        cursor.execute("""
            SELECT operator_id, line_id
            FROM operator_line
            WHERE operator_id = %s AND line_id = %s;
        """, (operator_id, line_id))
        existing_assignment = cursor.fetchone()

    if not errors:
        if not selected_line:
            errors['line_id'] = 'Selected line does not exist.'
        elif selected_line['is_retired']:
            errors['line_id'] = 'Inactive lines cannot be assigned.'

        if not selected_operator:
            errors['operator_id'] = 'Selected operator does not exist.'
        elif selected_operator['role_name'] != 'Operator':
            errors['operator_id'] = 'Only users with the Operator role can be assigned to lines.'
        elif not selected_operator['is_active']:
            errors['operator_id'] = 'Inactive operators cannot be assigned to lines.'

        if existing_assignment:
            errors['duplicate'] = 'This operator is already assigned to the selected line.'

    if errors:
        cursor.close()

        # Reload page data so the template can render again with validation messages
        cursor = db.get_cursor()

        cursor.execute("""
            SELECT
                l.id,
                l.name,
                l.line_type,
                l.is_retired
            FROM line l
            ORDER BY l.name;
        """)
        lines = cursor.fetchall()

        cursor.execute("""
            SELECT
                u.id,
                u.first_name,
                u.last_name,
                u.username,
                u.is_active
            FROM "user" u
            JOIN role r ON u.role_id = r.id
            WHERE r.name = 'Operator'
            ORDER BY u.first_name, u.last_name, u.username;
        """)
        operators = cursor.fetchall()

        cursor.execute("""
            SELECT
                l.id AS line_id,
                l.name AS line_name,
                l.line_type,
                l.is_retired,
                u.id AS operator_id,
                u.first_name,
                u.last_name,
                u.username,
                u.is_active,
                ol.assignment_date
            FROM line l
            LEFT JOIN operator_line ol ON l.id = ol.line_id
            LEFT JOIN "user" u ON ol.operator_id = u.id
            LEFT JOIN role r ON u.role_id = r.id
            WHERE u.id IS NULL OR r.name = 'Operator'
            ORDER BY l.name, u.first_name, u.last_name;
        """)
        assignment_rows = cursor.fetchall()
        cursor.close()

        grouped_lines = {}
        for line in lines:
            grouped_lines[line['id']] = {
                'line_id': line['id'],
                'line_name': line['name'],
                'line_type': line['line_type'],
                'is_retired': line['is_retired'],
                'operators': []
            }

        for row in assignment_rows:
            if row['operator_id'] is not None:
                grouped_lines[row['line_id']]['operators'].append({
                    'operator_id': row['operator_id'],
                    'full_name': f"{row['first_name']} {row['last_name']}",
                    'username': row['username'],
                    'is_active': row['is_active'],
                    'assignment_date': row['assignment_date']
                })

        return render_template(
            'admin/manage_line_assignments.html',
            grouped_lines=grouped_lines,
            lines=lines,
            operators=operators,
            assign_errors=errors,
            assign_form={
                'line_id': str(line_id) if line_id else '',
                'operator_id': str(operator_id) if operator_id else ''
            }
        )

    # Create the new assignment
    cursor.execute("""
        INSERT INTO operator_line (operator_id, line_id, assignment_date)
        VALUES (%s, %s, CURRENT_DATE);
    """, (operator_id, line_id))
    db.get_db().commit()
    cursor.close()

    flash('Line assigned successfully.', 'success')
    return redirect(url_for('manage_line_assignments'))


@app.route('/admin/line-assignments/reassign', methods=['POST'])
@login_required
@role_required('Admin')
def reassign_line_operator():
    """
    Reassign a line from one operator to another.

    Because operator_line uses a composite primary key
    (operator_id, line_id), reassignment is implemented as:
    1. delete the old assignment
    2. insert the new assignment
    """
    line_id = request.form.get('line_id', '').strip()
    old_operator_id = request.form.get('old_operator_id', '').strip()
    new_operator_id = request.form.get('new_operator_id', '').strip()

    try:
        line_id = int(line_id)
        old_operator_id = int(old_operator_id)
        new_operator_id = int(new_operator_id)
    except ValueError:
        flash('Invalid reassignment request.', 'danger')
        return redirect(url_for('manage_line_assignments'))

    if old_operator_id == new_operator_id:
        flash('Please choose a different operator for reassignment.', 'danger')
        return redirect(url_for('manage_line_assignments'))

    cursor = db.get_cursor()

    # Check line
    cursor.execute("""
        SELECT id, is_retired
        FROM line
        WHERE id = %s;
    """, (line_id,))
    selected_line = cursor.fetchone()

    # Check whether the original assignment exists
    cursor.execute("""
        SELECT operator_id, line_id
        FROM operator_line
        WHERE operator_id = %s AND line_id = %s;
    """, (old_operator_id, line_id))
    old_assignment = cursor.fetchone()

    # Check the new operator
    cursor.execute("""
        SELECT
            u.id,
            u.is_active,
            r.name AS role_name
        FROM "user" u
        JOIN role r ON u.role_id = r.id
        WHERE u.id = %s;
    """, (new_operator_id,))
    new_operator = cursor.fetchone()

    # Check whether the target assignment already exists
    cursor.execute("""
        SELECT operator_id, line_id
        FROM operator_line
        WHERE operator_id = %s AND line_id = %s;
    """, (new_operator_id, line_id))
    duplicate_target = cursor.fetchone()

    errors = []

    if not selected_line:
        errors.append('Selected line does not exist.')
    elif selected_line['is_retired']:
        errors.append('Inactive lines cannot be assigned.')

    if not old_assignment:
        errors.append('The original assignment does not exist.')

    if not new_operator:
        errors.append('Selected operator does not exist.')
    elif new_operator['role_name'] != 'Operator':
        errors.append('Only users with the Operator role can be assigned to lines.')
    elif not new_operator['is_active']:
        errors.append('Inactive operators cannot be assigned to lines.')

    if duplicate_target:
        errors.append('The new operator is already assigned to this line.')

    if errors:
        cursor.close()
        for error in errors:
            flash(error, 'danger')
        return redirect(url_for('manage_line_assignments'))

    # Delete the old assignment
    cursor.execute("""
        DELETE FROM operator_line
        WHERE operator_id = %s AND line_id = %s;
    """, (old_operator_id, line_id))

    # Insert the new assignment
    cursor.execute("""
        INSERT INTO operator_line (operator_id, line_id, assignment_date)
        VALUES (%s, %s, CURRENT_DATE);
    """, (new_operator_id, line_id))

    db.get_db().commit()
    cursor.close()

    flash('Line reassigned successfully.', 'success')
    return redirect(url_for('manage_line_assignments'))
