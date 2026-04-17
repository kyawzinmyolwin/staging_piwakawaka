# US14 Record Incidental Observations (Operator)

from datetime import datetime
from zoneinfo import ZoneInfo
from flask import render_template, request, redirect, url_for, flash, session
from piwakawaka import app, db
from piwakawaka.auth import login_required, role_required

_NZ = ZoneInfo('Pacific/Auckland')

OBS_TYPES = [
    'Bird sighting',
    'Predator track',
    'Predator sighting',
    'Native species track or sighting',
    'Other',
]


def _now_nz():
    """Current NZ time as a naive datetime for form comparisons."""
    return datetime.now(_NZ).replace(tzinfo=None)


# ── Add observation ──────────────────────────────────────────────────────────

@app.route('/lines/<int:line_id>/observations/add', methods=['GET', 'POST'])
@login_required
@role_required('Operator')
def add_observation(line_id):
    """
    US14: Record a new incidental observation for a specific line.

    Access rules:
    - Operator only (role_required enforces this)
    - Operator must be assigned to the line
    - Line must be active
    """
    cursor = db.get_cursor()

    # Verify line exists
    cursor.execute("""
        SELECT id, name, line_type, is_retired
        FROM line
        WHERE id = %s
    """, (line_id,))
    line = cursor.fetchone()

    if not line:
        cursor.close()
        flash('The selected line does not exist.', 'danger')
        return redirect(url_for('view_lines'))

    if line['is_retired']:
        cursor.close()
        flash('Cannot add an observation to an inactive line.', 'danger')
        return redirect(url_for('view_line_traps', line_id=line_id))

    # Verify operator is assigned to this line
    cursor.execute("""
        SELECT 1
        FROM operator_line
        WHERE operator_id = %s AND line_id = %s
    """, (session.get('user_id'), line_id))

    if not cursor.fetchone():
        cursor.close()
        flash('You can only add observations to lines assigned to you.', 'danger')
        return redirect(url_for('view_lines'))

    # Default form data for GET
    form_data = {
        'obs_date':    _now_nz().strftime('%Y-%m-%dT%H:%M'),
        'obs_type':    '',
        'description': '',
        'latitude':    '',
        'longitude':   '',
    }
    errors = {}

    if request.method == 'POST':
        form_data = {
            'obs_date':    request.form.get('obs_date',    '').strip(),
            'obs_type':    request.form.get('obs_type',    '').strip(),
            'description': request.form.get('description', '').strip(),
            'latitude':    request.form.get('latitude',    '').strip(),
            'longitude':   request.form.get('longitude',   '').strip(),
        }

        # --- Validate obs_date ---
        obs_date = None
        try:
            obs_date = datetime.strptime(form_data['obs_date'], '%Y-%m-%dT%H:%M')
        except (TypeError, ValueError):
            errors['obs_date'] = 'Please enter a valid date and time.'

        if obs_date is not None and obs_date > _now_nz():
            errors['obs_date'] = 'Observation date cannot be in the future.'

        # --- Validate obs_type ---
        if not form_data['obs_type']:
            errors['obs_type'] = 'Please select an observation type.'
        elif form_data['obs_type'] not in OBS_TYPES:
            errors['obs_type'] = 'Please select a valid observation type.'

        # --- Validate optional coordinates ---
        lat_value = None
        lng_value = None

        if form_data['latitude']:
            try:
                lat_value = float(form_data['latitude'])
                if not (-90 <= lat_value <= 90):
                    errors['latitude'] = 'Latitude must be between -90 and 90.'
            except ValueError:
                errors['latitude'] = 'Latitude must be a valid number.'

        if form_data['longitude']:
            try:
                lng_value = float(form_data['longitude'])
                if not (-180 <= lng_value <= 180):
                    errors['longitude'] = 'Longitude must be between -180 and 180.'
            except ValueError:
                errors['longitude'] = 'Longitude must be a valid number.'

        # --- Validate description length ---
        if len(form_data['description']) > 1000:
            errors['description'] = 'Description must be 1000 characters or fewer.'

        # --- Save if valid ---
        if not errors:
            try:
                cursor.execute("""
                    INSERT INTO incidental_obs
                        (operator_id, line_id, obs_date, obs_type, description, latitude, longitude)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                """, (
                    session.get('user_id'),
                    line_id,
                    obs_date,
                    form_data['obs_type'],
                    form_data['description'] or None,
                    lat_value,
                    lng_value,
                ))
                db.get_db().commit()
                cursor.close()
                flash('Observation recorded successfully.', 'success')
                return redirect(url_for('view_observations'))
            except Exception as e:
                db.get_db().rollback()
                app.logger.error(f'Error recording observation on line {line_id}: {e}')
                cursor.close()
                flash('A database error occurred while saving the observation. Please try again.', 'danger')
                return render_template(
                    'observations/add_observation.html',
                    line=line,
                    form_data=form_data,
                    errors={},
                    obs_types=OBS_TYPES,
                    max_date=_now_nz().strftime('%Y-%m-%dT%H:%M'),
                )

    cursor.close()
    return render_template(
        'observations/add_observation.html',
        line=line,
        form_data=form_data,
        errors=errors,
        obs_types=OBS_TYPES,
        max_date=_now_nz().strftime('%Y-%m-%dT%H:%M'),
    )


# ── View observations ────────────────────────────────────────────────────────
def _fetch_all_observations(cursor):
    """Fetch all incidental observations with related line and operator info."""
    cursor.execute("""
        SELECT
            io.id,
            io.obs_date,
            io.obs_type,
            io.description,
            io.latitude,
            io.longitude,
            l.name  AS line_name,
            l.id    AS line_id,
            u.username    AS operator_username,
            u.first_name  AS operator_first_name,
            u.last_name   AS operator_last_name
        FROM incidental_obs io
        JOIN line     l ON io.line_id     = l.id
        JOIN "user"   u ON io.operator_id = u.id
        ORDER BY io.obs_date DESC
    """)
    return cursor.fetchall()

def _fetch_observations_for_operator(cursor, operator_id):
    """Fetch all observations recorded by the given operator."""
    cursor.execute("""
        SELECT
            io.id,
            io.obs_date,
            io.obs_type,
            io.description,
            io.latitude,
            io.longitude,
            l.name  AS line_name,
            l.id    AS line_id,
            u.username    AS operator_username,
            u.first_name  AS operator_first_name,
            u.last_name   AS operator_last_name
        FROM incidental_obs io
        JOIN line   l ON io.line_id     = l.id
        JOIN "user" u ON io.operator_id = u.id
        WHERE io.operator_id = %s
        ORDER BY io.obs_date DESC
    """, (operator_id,))
    return cursor.fetchall()

@app.route('/observations')
@login_required
def view_observations():
    """
    US14: Display all recorded incidental observations.
    Accessible to all authenticated roles.
    """
    cursor = db.get_cursor()
    active_tab = request.args.get('tab', 'all')

    all_observations = _fetch_all_observations(cursor)
    my_observations = _fetch_observations_for_operator(cursor, session.get('user_id'))    
    cursor.close()

    return render_template('observations/list_observations.html',
                           all_observations=all_observations,
        my_observations=my_observations,
        active_tab=active_tab,
    )
