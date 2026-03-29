# US13 Add Trap Catch Records (Operator)
# US14 Record Incidental Observations (Operator)
# US15 Browse & Filter Catch Data
# US16 Edit Trap Catch Records (Operator)
# US17 Download Catch Data as CSV
from flask import render_template, request, redirect, url_for, flash, session
from datetime import datetime
from zoneinfo import ZoneInfo
from piwakawaka import app, db
from piwakawaka.auth import login_required, role_required

_NZ = ZoneInfo('Pacific/Auckland')

def _now_nz():
    """Current NZ time as a naive datetime (strips tzinfo for form comparison)."""
    return datetime.now(_NZ).replace(tzinfo=None)


@app.route('/catches')
@login_required
def catches():
    # --- Get filter values from URL query params ---
    active_tab     = request.args.get('tab', 'all') # default to 'all' if no tab specified
    filter_line    = request.args.get('line', '')
    filter_species = request.args.get('species', '')
    filter_bait    = request.args.get('bait', '')
    filter_from    = request.args.get('date_from', '')
    filter_to      = request.args.get('date_to', '')

    # --- Build query dynamically based on active filters ---
    query = '''
        SELECT
            tc.id,
            l.name        AS line_name,
            t.code        AS trap_code,
            s.name        AS species,
            bt.name       AS bait_type,
            tc.strikes,
            tc.date_checked,
            tc.recorded_by  AS recorded_by_id,
            tc.sex,
            tc.maturity,
            ts.name       AS status,
            tcon.name     AS condition,
            tc.rebaited,
            tc.notes,
            u.username    AS recorded_by
        FROM trap_catch tc
        JOIN trap           t    ON tc.trap_id      = t.id
        JOIN line           l    ON t.line_id        = l.id
        JOIN species        s    ON tc.species_id    = s.id
        JOIN bait_type      bt   ON tc.bait_type_id  = bt.id
        JOIN trap_status    ts   ON tc.status_id     = ts.id
        JOIN trap_condition tcon ON tc.condition_id  = tcon.id
        LEFT JOIN "user"    u    ON tc.recorded_by   = u.id
        WHERE 1=1
    '''
    params = []

    # Tab filter — "My Catches" restricts to the logged-in user's records
    if active_tab == 'mine':
        query += ' AND tc.recorded_by = %s'
        params.append(session.get('user_id'))

    if filter_line:
        query += ' AND l.id = %s'
        params.append(filter_line)
    if filter_species:
        query += ' AND s.id = %s'
        params.append(filter_species)
    if filter_bait:
        query += ' AND bt.id = %s'
        params.append(filter_bait)
    if filter_from:
        query += ' AND tc.date_checked >= %s'
        params.append(filter_from)
    if filter_to:
        query += ' AND tc.date_checked <= %s'
        params.append(filter_to + ' 23:59:59')

    query += ' ORDER BY tc.date_checked DESC'

    # --- Fetch results and dropdown options ---
    cursor = db.get_cursor()
    cursor.execute(query, params)
    records = cursor.fetchall()

    cursor.execute('SELECT id, name FROM line WHERE is_retired = FALSE ORDER BY name')
    lines = cursor.fetchall()

    cursor.execute('SELECT id, name FROM species ORDER BY name')
    species_list = cursor.fetchall()

    cursor.execute('SELECT id, name FROM bait_type ORDER BY name')
    bait_list = cursor.fetchall()

    # Lines available for adding catch records (Operator: assigned lines; Admin: all active lines)
    assignable_lines = []
    user_role = session.get('role')
    if user_role == 'Admin':
        assignable_lines = lines  # Admin can add to any active line
    elif user_role == 'Operator':
        cursor.execute(
            '''SELECT l.id, l.name
               FROM line l
               JOIN operator_line ol ON l.id = ol.line_id
               WHERE ol.operator_id = %s AND l.is_retired = FALSE
               ORDER BY l.name''',
            (session.get('user_id'),)
        )
        assignable_lines = cursor.fetchall()

    cursor.close()

    return render_template('catches/list.html',
                           records=records,
                           lines=lines,
                           species_list=species_list,
                           bait_list=bait_list,
                           assignable_lines=assignable_lines,
                           active_tab=active_tab,
                           filter_line=filter_line,
                           filter_species=filter_species,
                           filter_bait=filter_bait,
                           filter_from=filter_from,
                           filter_to=filter_to)


SEX_OPTIONS = ['Male', 'Female']
MATURITY_OPTIONS = ['Juvenile', 'Adult']
REBAITED_OPTIONS = ['Yes', 'No']


def get_lookup_options(cursor):
    cursor.execute('SELECT id, name FROM species ORDER BY name')
    species_options = cursor.fetchall()

    cursor.execute('SELECT id, name FROM trap_status ORDER BY name')
    status_options = cursor.fetchall()

    cursor.execute('SELECT id, name FROM bait_type ORDER BY name')
    bait_type_options = cursor.fetchall()

    cursor.execute('SELECT id, name FROM trap_condition ORDER BY name')
    condition_options = cursor.fetchall()

    return species_options, status_options, bait_type_options, condition_options


def parse_datetime_local(value):
    try:
        return datetime.strptime(value, '%Y-%m-%dT%H:%M')
    except (TypeError, ValueError):
        return None


def get_option_id_by_name(options, target_name):
    for option in options:
        if option['name'] == target_name:
            return option['id']
    return None


def operator_has_line_assignment(cursor, user_id, line_id):
    cursor.execute(
        '''SELECT 1
           FROM operator_line
           WHERE operator_id = %s AND line_id = %s''',
        (user_id, line_id)
    )
    return cursor.fetchone() is not None


@app.route('/lines/<int:line_id>/catches/add', methods=['GET', 'POST'])
@login_required
@role_required('Operator', 'Admin')
def add_catch(line_id):
    cursor = db.get_cursor()

    cursor.execute(
        '''SELECT id, name, line_type, is_retired
           FROM line
           WHERE id = %s''',
        (line_id,)
    )
    line = cursor.fetchone()

    if not line:
        cursor.close()
        flash('The selected line does not exist.', 'danger')
        return redirect(url_for('view_lines'))

    if line['is_retired']:
        cursor.close()
        flash('Cannot add a catch record to an inactive line.', 'danger')
        return redirect(url_for('view_line_traps', line_id=line_id))

    is_admin = session.get('role') == 'Admin'
    if not is_admin and not operator_has_line_assignment(cursor, session.get('user_id'), line_id):
        cursor.close()
        flash('You can only add catch records to lines assigned to you.', 'danger')
        return redirect(url_for('view_lines'))

    cursor.execute(
        '''SELECT id, code
           FROM trap
           WHERE line_id = %s AND is_retired = FALSE
           ORDER BY code''',
        (line_id,)
    )
    trap_options = cursor.fetchall()

    species_options, status_options, bait_type_options, condition_options = get_lookup_options(cursor)

    none_species_id = get_option_id_by_name(species_options, 'None')
    none_bait_type_id = get_option_id_by_name(bait_type_options, 'None')

    if none_species_id is None or none_bait_type_id is None:
        cursor.close()
        flash('System configuration error: required "None" option is missing.', 'danger')
        return redirect(url_for('view_line_traps', line_id=line_id))

    form_data = {
        'trap_id': '',
        'date_checked': _now_nz().strftime('%Y-%m-%dT%H:%M'),
        'species_id': '',
        'sex': '',
        'maturity': '',
        'status_id': '',
        'rebaited': '',
        'bait_type_id': '',
        'condition_id': '',
        'strikes': '',
        'notes': '',
    }
    errors = {}

    if request.method == 'POST':
        form_data = {
            'trap_id': request.form.get('trap_id', '').strip(),
            'date_checked': request.form.get('date_checked', '').strip(),
            'species_id': request.form.get('species_id', '').strip(),
            'sex': request.form.get('sex', '').strip(),
            'maturity': request.form.get('maturity', '').strip(),
            'status_id': request.form.get('status_id', '').strip(),
            'rebaited': request.form.get('rebaited', '').strip(),
            'bait_type_id': request.form.get('bait_type_id', '').strip(),
            'condition_id': request.form.get('condition_id', '').strip(),
            'strikes': request.form.get('strikes', '').strip(),
            'notes': request.form.get('notes', '').strip(),
        }

        valid_trap_ids = {str(option['id']) for option in trap_options}
        valid_species_ids = {str(option['id']) for option in species_options}
        valid_status_ids = {str(option['id']) for option in status_options}
        valid_bait_type_ids = {str(option['id']) for option in bait_type_options}
        valid_condition_ids = {str(option['id']) for option in condition_options}

        if form_data['trap_id'] not in valid_trap_ids:
            errors['trap_id'] = 'Please select a valid trap code.'

        date_checked = parse_datetime_local(form_data['date_checked'])
        if not date_checked:
            errors['date_checked'] = 'Please enter a valid date and time.'
        elif date_checked > _now_nz():
            errors['date_checked'] = 'Date checked cannot be in the future.'

        if form_data['species_id'] not in valid_species_ids:
            errors['species_id'] = 'Please select a valid species.'

        if form_data['sex'] and form_data['sex'] not in SEX_OPTIONS:
            errors['sex'] = 'Please choose a valid sex option.'

        if form_data['maturity'] and form_data['maturity'] not in MATURITY_OPTIONS:
            errors['maturity'] = 'Please choose a valid maturity option.'

        if form_data['status_id'] not in valid_status_ids:
            errors['status_id'] = 'Please select a valid status.'

        if form_data['rebaited'] not in REBAITED_OPTIONS:
            errors['rebaited'] = 'Please choose whether the trap was rebaited.'

        if form_data['condition_id'] not in valid_condition_ids:
            errors['condition_id'] = 'Please select a valid trap condition.'

        selected_species_id = None
        if form_data['species_id'] in valid_species_ids:
            selected_species_id = int(form_data['species_id'])

        selected_bait_type_id = None
        if form_data['rebaited'] == 'No':
            selected_bait_type_id = none_bait_type_id
        elif form_data['bait_type_id'] not in valid_bait_type_ids:
            errors['bait_type_id'] = 'Please select a valid bait type.'
        else:
            selected_bait_type_id = int(form_data['bait_type_id'])
            if selected_bait_type_id == none_bait_type_id:
                errors['bait_type_id'] = 'Please select a bait type when rebaited is Yes.'

        try:
            strikes = int(form_data['strikes'])
            if strikes < 0:
                errors['strikes'] = 'Strikes must be 0 or greater.'
        except (TypeError, ValueError):
            errors['strikes'] = 'Strikes must be a whole number.'
            strikes = None

        if selected_species_id == none_species_id and strikes is not None:
            if strikes >= 1:
                errors['species_id'] = 'Please select a species when strikes is 1 or more.'
            else:
                strikes = 0

        if selected_species_id != none_species_id and strikes == 0 and 'species_id' not in errors:
            pass

        if len(form_data['notes']) > 1000:
            errors['notes'] = 'Notes must be 1000 characters or fewer.'

        if not errors:
            try:
                cursor.execute(
                    '''INSERT INTO trap_catch
                       (trap_id, date_checked, recorded_by, species_id, sex, maturity,
                        status_id, rebaited, bait_type_id, condition_id, strikes, notes)
                       VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)''',
                    (
                        int(form_data['trap_id']),
                        date_checked,
                        session.get('user_id'),
                        selected_species_id,
                        form_data['sex'] or None,
                        form_data['maturity'] or None,
                        int(form_data['status_id']),
                        form_data['rebaited'] == 'Yes',
                        selected_bait_type_id,
                        int(form_data['condition_id']),
                        strikes,
                        form_data['notes'] or None,
                    )
                )
                db.get_db().commit()
                cursor.close()
                flash('Trap catch record added successfully.', 'success')
                return redirect(url_for('catches', tab='mine'))
            except Exception as e:
                db.get_db().rollback()
                app.logger.error(f'Error creating trap catch on line {line_id}: {e}')
                errors['database'] = 'A database error occurred while saving the record.'

    cursor.close()

    return render_template(
        'catches/add_catch.html',
        line=line,
        trap_options=trap_options,
        form_data=form_data,
        errors=errors,
        species_options=species_options,
        status_options=status_options,
        bait_type_options=bait_type_options,
        condition_options=condition_options,
        sex_options=SEX_OPTIONS,
        maturity_options=MATURITY_OPTIONS,
        rebaited_options=REBAITED_OPTIONS,
    )


@app.route('/catches/<int:catch_id>')
@login_required
def view_catch_detail(catch_id):
    try:
        cursor = db.get_cursor()
        cursor.execute(
            '''SELECT tc.id,
                      tc.trap_id,
                      tc.date_checked,
                      tc.recorded_by,
                      tc.sex,
                      tc.maturity,
                      tc.rebaited,
                      tc.strikes,
                      tc.notes,
                      t.code AS trap_code,
                      s.name AS species,
                      ts.name AS status,
                      bt.name AS bait_type,
                      tcnd.name AS trap_condition,
                      u.username AS recorded_by_username
               FROM trap_catch tc
               JOIN trap t ON tc.trap_id = t.id
               JOIN species s ON tc.species_id = s.id
               JOIN trap_status ts ON tc.status_id = ts.id
               JOIN bait_type bt ON tc.bait_type_id = bt.id
               JOIN trap_condition tcnd ON tc.condition_id = tcnd.id
               LEFT JOIN "user" u ON tc.recorded_by = u.id
               WHERE tc.id = %s''',
            (catch_id,)
        )
        catch_record = cursor.fetchone()
        cursor.close()
    except Exception as e:
        app.logger.error(f'Error loading trap catch {catch_id}: {e}')
        flash('Unable to load trap catch record right now.', 'danger')
        return redirect(url_for('catches'))

    if not catch_record:
        flash('Trap catch record not found.', 'warning')
        return redirect(url_for('catches'))

    can_edit = (
        session.get('role') == 'Operator'
        and catch_record['recorded_by'] == session.get('user_id')
    )

    return render_template('catches/view_catch_detail.html', catch_record=catch_record, can_edit=can_edit)


@app.route('/catches/<int:catch_id>/edit', methods=['GET', 'POST'])
@login_required
@role_required('Operator')
def edit_catch(catch_id):

    cursor = db.get_cursor()

    # Fetch user's account creation date to validate date_checked against it
    cursor.execute("""
    SELECT created_at FROM "user" WHERE id = %s
    """, (session.get('user_id'),))
    user = cursor.fetchone()
    account_created = user['created_at']

    # Format for HTML datetime-local input (YYYY-MM-DDTHH:MM)
    min_date = user['created_at'].strftime('%Y-%m-%dT%H:%M')
    max_date = _now_nz().strftime('%Y-%m-%dT%H:%M')

    cursor.execute(
        '''SELECT tc.id, tc.trap_id, tc.date_checked, tc.recorded_by,
                  tc.species_id, tc.sex, tc.maturity, tc.status_id,
                  tc.rebaited, tc.bait_type_id, tc.condition_id, tc.strikes, tc.notes,
                  t.code AS trap_code
           FROM trap_catch tc
           JOIN trap t ON tc.trap_id = t.id
           WHERE tc.id = %s''',
        (catch_id,)
    )
    catch_record = cursor.fetchone()

    if not catch_record:
        cursor.close()
        flash('Trap catch record not found.', 'warning')
        return redirect(url_for('catches'))

    if catch_record['recorded_by'] != session.get('user_id'):
        cursor.close()
        flash('You can only edit trap catch records that you created.', 'danger')
        return redirect(url_for('view_catch_detail', catch_id=catch_id))

    species_options, status_options, bait_type_options, condition_options = get_lookup_options(cursor)

    if request.method == 'POST':
        form_data = {
            'date_checked': request.form.get('date_checked', '').strip(),
            'species_id':   request.form.get('species_id', '').strip(),
            'sex':          request.form.get('sex', '').strip(),
            'maturity':     request.form.get('maturity', '').strip(),
            'status_id':    request.form.get('status_id', '').strip(),
            'rebaited':     request.form.get('rebaited', '').strip(),
            'bait_type_id': request.form.get('bait_type_id', '').strip(),
            'condition_id': request.form.get('condition_id', '').strip(),
            'strikes':      request.form.get('strikes', '').strip(),
            'notes':        request.form.get('notes', '').strip(),
        }

        errors = {}

        # Parse and validate date once
        date_checked = parse_datetime_local(form_data['date_checked'])
        if not date_checked:
            errors['date_checked'] = 'Please enter a valid date and time.'
        else:
            if date_checked > _now_nz():
                errors['date_checked'] = 'Date checked cannot be in the future.'
            elif date_checked < account_created:
                errors['date_checked'] = 'Date checked cannot be before your account was created.'

        valid_species_ids = {str(option['id']) for option in species_options}
        if form_data['species_id'] not in valid_species_ids:
            errors['species_id'] = 'Please select a valid species.'

        if form_data['sex'] and form_data['sex'] not in SEX_OPTIONS:
            errors['sex'] = 'Please choose a valid sex option.'

        if form_data['maturity'] and form_data['maturity'] not in MATURITY_OPTIONS:
            errors['maturity'] = 'Please choose a valid maturity option.'

        valid_status_ids = {str(option['id']) for option in status_options}
        if form_data['status_id'] not in valid_status_ids:
            errors['status_id'] = 'Please select a valid status.'

        if form_data['rebaited'] not in REBAITED_OPTIONS:
            errors['rebaited'] = 'Please choose whether the trap was rebaited.'

        valid_bait_type_ids = {str(option['id']) for option in bait_type_options}
        if form_data['bait_type_id'] not in valid_bait_type_ids:
            errors['bait_type_id'] = 'Please select a valid bait type.'

        valid_condition_ids = {str(option['id']) for option in condition_options}
        if form_data['condition_id'] not in valid_condition_ids:
            errors['condition_id'] = 'Please select a valid trap condition.'

        try:
            strikes = int(form_data['strikes'])
            if strikes < 0:
                errors['strikes'] = 'Strikes must be 0 or greater.'
        except (TypeError, ValueError):
            errors['strikes'] = 'Strikes must be a whole number.'

        if len(form_data['notes']) > 1000:
            errors['notes'] = 'Notes must be 1000 characters or fewer.'

        if errors:
            cursor.close()
            return render_template(
                'catches/edit_catch.html',
                catch_id=catch_id,
                trap_id=catch_record['trap_id'],
                trap_code=catch_record['trap_code'],
                form_data=form_data,
                errors=errors,
                species_options=species_options,
                status_options=status_options,
                bait_type_options=bait_type_options,
                condition_options=condition_options,
                sex_options=SEX_OPTIONS,
                maturity_options=MATURITY_OPTIONS,
                rebaited_options=REBAITED_OPTIONS,
                min_date=min_date,
                max_date=max_date,
            )

        try:
            cursor.execute(
                '''UPDATE trap_catch
                   SET date_checked = %s,
                       species_id = %s,
                       sex = %s,
                       maturity = %s,
                       status_id = %s,
                       rebaited = %s,
                       bait_type_id = %s,
                       condition_id = %s,
                       strikes = %s,
                       notes = %s
                   WHERE id = %s''',
                (
                    date_checked,
                    int(form_data['species_id']),
                    form_data['sex'] or None,
                    form_data['maturity'] or None,
                    int(form_data['status_id']),
                    form_data['rebaited'] == 'Yes',
                    int(form_data['bait_type_id']),
                    int(form_data['condition_id']),
                    strikes,
                    form_data['notes'] or None,
                    catch_id,
                )
            )
            db.get_db().commit()
            cursor.close()
            flash('Trap catch record updated successfully.', 'success')
            return redirect(url_for('view_catch_detail', catch_id=catch_id))
        except Exception as e:
            db.get_db().rollback()
            app.logger.error(f'Error updating trap catch {catch_id}: {e}')
            cursor.close()
            flash('A database error occurred while updating the record.', 'danger')
            return render_template(
                'catches/edit_catch.html',
                catch_id=catch_id,
                trap_id=catch_record['trap_id'],
                trap_code=catch_record['trap_code'],
                form_data=form_data,
                errors={},
                species_options=species_options,
                status_options=status_options,
                bait_type_options=bait_type_options,
                condition_options=condition_options,
                sex_options=SEX_OPTIONS,
                maturity_options=MATURITY_OPTIONS,
                rebaited_options=REBAITED_OPTIONS,
                min_date=min_date,
                max_date=max_date,
            )

    form_data = {
        'date_checked': catch_record['date_checked'].strftime('%Y-%m-%dT%H:%M') if catch_record['date_checked'] else '',
        'species_id':   str(catch_record['species_id']),
        'sex':          catch_record['sex'] or '',
        'maturity':     catch_record['maturity'] or '',
        'status_id':    str(catch_record['status_id']),
        'rebaited':     'Yes' if catch_record['rebaited'] else 'No',
        'bait_type_id': str(catch_record['bait_type_id']),
        'condition_id': str(catch_record['condition_id']),
        'strikes':      str(catch_record['strikes']),
        'notes':        catch_record['notes'] or '',
    }

    cursor.close()

    return render_template(
        'catches/edit_catch.html',
        catch_id=catch_id,
        trap_id=catch_record['trap_id'],
        form_data=form_data,
        errors={},
        species_options=species_options,
        status_options=status_options,
        bait_type_options=bait_type_options,
        condition_options=condition_options,
        sex_options=SEX_OPTIONS,
        maturity_options=MATURITY_OPTIONS,
        rebaited_options=REBAITED_OPTIONS,
        min_date=min_date,
        max_date=max_date,
    )
