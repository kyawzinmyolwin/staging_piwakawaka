# US21 — View Graphical Summaries
import json
from flask import render_template, request
from piwakawaka import app, db
from piwakawaka.auth import login_required


@app.route('/reports')
@login_required
def reports():
    cursor = db.get_cursor()

    # ── Filter params ────────────────────────────────────────────
    date_from  = request.args.get('date_from', '').strip()
    date_to    = request.args.get('date_to', '').strip()
    species_id = request.args.get('species_id', '').strip()

    where_parts = ['tc.strikes > 0']
    params_base = []

    if date_from:
        where_parts.append('tc.date_checked >= %s')
        params_base.append(date_from)
    if date_to:
        where_parts.append('tc.date_checked <= %s')
        params_base.append(date_to + ' 23:59:59')
    if species_id:
        where_parts.append('tc.species_id = %s')
        params_base.append(species_id)

    where = 'WHERE ' + ' AND '.join(where_parts)

    # ── Summary stats ────────────────────────────────────────────
    cursor.execute(
        f'SELECT COALESCE(SUM(tc.strikes), 0) AS total FROM trap_catch tc {where}',
        params_base
    )
    total_strikes = int(cursor.fetchone()['total'])

    cursor.execute(
        f'''SELECT COUNT(DISTINCT tc.species_id) AS cnt
            FROM trap_catch tc {where}''',
        params_base
    )
    species_count = int(cursor.fetchone()['cnt'])

    cursor.execute(
        f'''SELECT COUNT(DISTINCT t.line_id) AS cnt
            FROM trap_catch tc
            JOIN trap t ON tc.trap_id = t.id
            {where}''',
        params_base
    )
    active_lines = int(cursor.fetchone()['cnt'])

    # Total records (not just strikes>0) for "checks" count
    where_all_parts = ['1=1']
    params_all = []
    if date_from:
        where_all_parts.append('date_checked >= %s')
        params_all.append(date_from)
    if date_to:
        where_all_parts.append('date_checked <= %s')
        params_all.append(date_to + ' 23:59:59')
    cursor.execute(
        'SELECT COUNT(*) AS cnt FROM trap_catch WHERE ' + ' AND '.join(where_all_parts),
        params_all
    )
    total_checks = int(cursor.fetchone()['cnt'])

    # ── Top species ──────────────────────────────────────────────
    cursor.execute(
        f'''SELECT s.name, COALESCE(SUM(tc.strikes), 0) AS total
            FROM trap_catch tc
            JOIN species s ON tc.species_id = s.id
            {where}
            GROUP BY s.name
            ORDER BY total DESC
            LIMIT 10''',
        params_base
    )
    species_rows = cursor.fetchall()

    # ── Line rankings ────────────────────────────────────────────
    cursor.execute(
        f'''SELECT l.name, COALESCE(SUM(tc.strikes), 0) AS total
            FROM trap_catch tc
            JOIN trap t ON tc.trap_id = t.id
            JOIN line l ON t.line_id  = l.id
            {where}
            GROUP BY l.name
            ORDER BY total DESC''',
        params_base
    )
    line_rows = cursor.fetchall()

    # ── Monthly trend ────────────────────────────────────────────
    cursor.execute(
        f'''SELECT TO_CHAR(tc.date_checked, 'YYYY-MM') AS month,
                   COALESCE(SUM(tc.strikes), 0) AS total
            FROM trap_catch tc
            {where}
            GROUP BY month
            ORDER BY month''',
        params_base
    )
    trend_rows = cursor.fetchall()

    # ── Species list for filter ──────────────────────────────────
    cursor.execute('SELECT id, name FROM species ORDER BY name')
    all_species = cursor.fetchall()
    cursor.close()

    # ── Serialise for Chart.js ───────────────────────────────────
    trend_chart = {
        'labels': [r['month'] for r in trend_rows],
        'data':   [int(r['total']) for r in trend_rows],
    }

    # Line rankings with percentage for progress bars
    max_line = max((int(r['total']) for r in line_rows), default=1)
    line_rankings = [
        {
            'name':    r['name'],
            'total':   int(r['total']),
            'pct':     round(int(r['total']) / max_line * 100),
        }
        for r in line_rows
    ]

    has_data = total_strikes > 0 or total_checks > 0

    return render_template(
        'reports/graphs.html',
        # stats
        total_strikes    = total_strikes,
        species_count    = species_count,
        active_lines     = active_lines,
        total_checks     = total_checks,
        # charts
        species_rows     = species_rows,
        line_rankings    = line_rankings,
        trend_chart      = json.dumps(trend_chart),
        has_data         = has_data,
        # filter
        all_species      = all_species,
        date_from        = date_from,
        date_to          = date_to,
        selected_species = species_id,
    )
