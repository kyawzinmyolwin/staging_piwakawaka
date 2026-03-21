"""Reusable lookup queries shared across route modules."""


def get_species_options(cursor):
    cursor.execute('SELECT id, name FROM species ORDER BY name')
    return cursor.fetchall()


def get_trap_status_options(cursor):
    cursor.execute('SELECT id, name FROM trap_status ORDER BY name')
    return cursor.fetchall()


def get_bait_type_options(cursor):
    cursor.execute('SELECT id, name FROM bait_type ORDER BY name')
    return cursor.fetchall()


def get_trap_condition_options(cursor):
    cursor.execute('SELECT id, name FROM trap_condition ORDER BY name')
    return cursor.fetchall()


def get_catch_lookup_options(cursor):
    """Return all dropdown lookup options for catch forms."""
    return (
        get_species_options(cursor),
        get_trap_status_options(cursor),
        get_bait_type_options(cursor),
        get_trap_condition_options(cursor),
    )


def get_lines_for_assignment(cursor):
    cursor.execute(
        """
        SELECT
            l.id,
            l.name,
            l.line_type,
            l.is_retired
        FROM line l
        ORDER BY l.name;
        """
    )
    return cursor.fetchall()


def get_operators_for_assignment(cursor):
    cursor.execute(
        """
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
        """
    )
    return cursor.fetchall()


def get_assignment_rows(cursor):
    cursor.execute(
        """
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
        """
    )
    return cursor.fetchall()


def build_grouped_line_assignments(lines, assignment_rows):
    grouped_lines = {}
    for line in lines:
        grouped_lines[line['id']] = {
            'line_id': line['id'],
            'line_name': line['name'],
            'line_type': line['line_type'],
            'is_retired': line['is_retired'],
            'operators': [],
        }

    for row in assignment_rows:
        if row['operator_id'] is not None:
            grouped_lines[row['line_id']]['operators'].append(
                {
                    'operator_id': row['operator_id'],
                    'full_name': f"{row['first_name']} {row['last_name']}",
                    'username': row['username'],
                    'is_active': row['is_active'],
                    'assignment_date': row['assignment_date'],
                }
            )

    return grouped_lines
