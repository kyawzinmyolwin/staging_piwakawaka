from flask import render_template, session
from piwakawaka import app
from piwakawaka.auth import login_required


@app.route('/')
def home():
    return render_template('home.html')


@app.route('/dashboard')
@login_required
def dashboard():
    role = session.get('role')
    if role == 'Admin':
        return render_template('dashboard_admin.html')
    elif role == 'Operator':
        return render_template('dashboard_operator.html')
    else:
        return render_template('dashboard_observer.html')


@app.after_request
def add_header(response):
    """Prevent browser caching so sensitive pages can't be viewed via back
    button after logout."""
    response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, post-check=0, pre-check=0, max-age=0'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '-1'
    return response
