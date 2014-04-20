from flask import Flask
from flask_peewee.admin import Admin
from flask_peewee.db import Database
from flask.ext.cache import Cache

from .auth import Auth
from .models import register_admin



app = Flask(__name__)

# loads configuration
app.config.from_pyfile("app.cfg")
app.config.from_pyfile("app-dev.cfg", silent=True)

# initialize database
db = Database(app)

# initialize cache
cache = Cache(app)

# initialize auth and admin
auth = Auth(app, db)
admin = Admin(app, auth)
register_admin(admin)
admin.setup()

