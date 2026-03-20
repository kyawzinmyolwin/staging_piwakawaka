import os
from flask import Flask

app = Flask(__name__, template_folder='../templates', static_folder='../static')

app.secret_key = os.environ.get('SECRET_KEY', 'pflu-secret-key-change-in-production')

# Set up database connection using connect module and db abstraction layer.
from piwakawaka import connect
from piwakawaka import db
db.init_db(app, connect.dbuser, connect.dbpass, connect.dbhost, connect.dbname, connect.dbport)

# Include all modules that define route-handling functions.
from piwakawaka import home
from piwakawaka import auth
from piwakawaka import profile
from piwakawaka import lines
from piwakawaka import catches
from piwakawaka import admin
