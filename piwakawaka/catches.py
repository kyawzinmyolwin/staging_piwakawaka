# US13 Add Trap Catch Records (Operator)
# US14 Record Incidental Observations (Operator)
# US15 Browse & Filter Catch Data
# US16 Edit Trap Catch Records (Operator)
# US17 Download Catch Data as CSV
from flask import render_template, request, redirect, url_for, flash
from piwakawaka import app, db
from piwakawaka.auth import login_required, role_required


@app.route('/catches')
@login_required
def catches():
    # --- Get filter values from URL query params ---
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

    cursor.close()

    return render_template('catches/list.html',
                           records=records,
                           lines=lines,
                           species_list=species_list,
                           bait_list=bait_list,
                           filter_line=filter_line,
                           filter_species=filter_species,
                           filter_bait=filter_bait,
                           filter_from=filter_from,
                           filter_to=filter_to)
