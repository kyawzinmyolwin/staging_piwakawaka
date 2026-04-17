# US18 Manage Species (Admin)

from flask import render_template, request, redirect, url_for, flash
from piwakawaka import app, db
from piwakawaka.auth import login_required, role_required


# ── List + Add ───────────────────────────────────────────────────────────────

@app.route('/admin/species', methods=['GET', 'POST'])
@login_required
@role_required('Admin')
def manage_species():
    """
    Display all species and handle adding a new one.

    POST validation:
    - name is required
    - name must be unique (case-insensitive)
    """
    cursor = db.get_cursor()
    errors = {}
    form_data = {'name': ''}

    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        form_data['name'] = name

        if not name:
            errors['name'] = 'Species name is required.'
        elif len(name) > 50:
            errors['name'] = 'Species name must be 50 characters or fewer.'
        else:
            # Case-insensitive duplicate check
            cursor.execute("""
                SELECT id FROM species
                WHERE LOWER(name) = LOWER(%s)
            """, (name,))
            if cursor.fetchone():
                errors['name'] = 'A species with this name already exists.'

        if not errors:
            cursor.execute("""
                INSERT INTO species (name) VALUES (%s)
            """, (name,))
            db.get_db().commit()
            cursor.close()
            flash(f"Species '{name}' added successfully.", 'success')
            return redirect(url_for('manage_species'))

    cursor.execute("SELECT id, name FROM species ORDER BY name")
    species_list = cursor.fetchall()
    cursor.close()

    return render_template(
        'admin/manage_species.html',
        species_list=species_list,
        errors=errors,
        form_data=form_data,
    )


# ── Edit ─────────────────────────────────────────────────────────────────────

@app.route('/admin/species/<int:species_id>/edit', methods=['POST'])
@login_required
@role_required('Admin')
def edit_species(species_id):
    """
    Update the name of an existing species.

    Validation:
    - species must exist
    - new name is required
    - new name must be unique (excluding the species being edited)
    """
    new_name = request.form.get('name', '').strip()

    if not new_name:
        flash('Species name is required.', 'danger')
        return redirect(url_for('manage_species'))

    if len(new_name) > 50:
        flash('Species name must be 50 characters or fewer.', 'danger')
        return redirect(url_for('manage_species'))

    cursor = db.get_cursor()

    cursor.execute("SELECT id, name FROM species WHERE id = %s", (species_id,))
    species = cursor.fetchone()

    if not species:
        cursor.close()
        flash('Species not found.', 'danger')
        return redirect(url_for('manage_species'))

    # Duplicate check — exclude self
    cursor.execute("""
        SELECT id FROM species
        WHERE LOWER(name) = LOWER(%s) AND id <> %s
    """, (new_name, species_id))
    if cursor.fetchone():
        cursor.close()
        flash(f"A species named '{new_name}' already exists.", 'danger')
        return redirect(url_for('manage_species'))

    cursor.execute("UPDATE species SET name = %s WHERE id = %s", (new_name, species_id))
    db.get_db().commit()
    cursor.close()

    flash(f"Species updated to '{new_name}' successfully.", 'success')
    return redirect(url_for('manage_species'))


# ── Delete ───────────────────────────────────────────────────────────────────

@app.route('/admin/species/<int:species_id>/delete', methods=['POST'])
@login_required
@role_required('Admin')
def delete_species(species_id):
    """
    Delete a species if it has never been referenced in a trap catch record.

    Rules:
    - species must exist
    - deletion is blocked if any trap_catch row references this species_id
    """
    cursor = db.get_cursor()

    cursor.execute("SELECT id, name FROM species WHERE id = %s", (species_id,))
    species = cursor.fetchone()

    if not species:
        cursor.close()
        flash('Species not found.', 'danger')
        return redirect(url_for('manage_species'))

    # FK check — block deletion if referenced in trap_catch
    cursor.execute("""
        SELECT COUNT(*) AS catch_count
        FROM trap_catch
        WHERE species_id = %s
    """, (species_id,))
    row = cursor.fetchone()

    if row['catch_count'] > 0:
        cursor.close()
        flash(
            f"'{species['name']}' cannot be deleted because it is linked to "
            f"{row['catch_count']} existing catch record"
            f"{'s' if row['catch_count'] != 1 else ''}.",
            'danger'
        )
        return redirect(url_for('manage_species'))

    cursor.execute("DELETE FROM species WHERE id = %s", (species_id,))
    db.get_db().commit()
    cursor.close()

    flash(f"Species '{species['name']}' deleted successfully.", 'success')
    return redirect(url_for('manage_species'))
