"""PostgreSQL database connectivity for the Flask app.

Based on the Flask "Define and Access the Database" tutorial pattern.
Provides a request-scoped database connection cached in Flask's `g` object,
automatically closed at the end of each request.

Usage:
    from piwakawaka import db

    # In a route:
    cursor = db.get_cursor()
    cursor.execute('SELECT ...')
    results = cursor.fetchall()
    cursor.close()
"""
import psycopg2
import psycopg2.extras
from flask import Flask, g

connection_params = {}


def init_db(app: Flask, user: str, password: str, host: str, database: str,
            port: int = 5432):
    """Initialise database connectivity for the Flask app.

    Must be called once during app setup before any routes are handled.
    """
    connection_params['user'] = user
    connection_params['password'] = password
    connection_params['host'] = host
    connection_params['database'] = database
    connection_params['port'] = port

    app.teardown_appcontext(close_db)


def get_db():
    """Return the database connection for the current request.

    Creates a new connection on first call within a request; subsequent calls
    return the same connection. Closed automatically at end of request.
    """
    if 'db' not in g:
        conn = psycopg2.connect(
            user=connection_params['user'],
            password=connection_params['password'],
            host=connection_params['host'],
            dbname=connection_params['database'],
            port=connection_params['port']
        )
        g.db = conn
    return g.db


def get_cursor():
    """Return a new RealDictCursor for the current request's connection.

    Remember to close the cursor when done.
    """
    return get_db().cursor(cursor_factory=psycopg2.extras.RealDictCursor)


def close_db(exception=None):
    """Close the database connection at the end of the request."""
    db = g.pop('db', None)
    if db is not None:
        db.close()
