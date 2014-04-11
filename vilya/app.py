from flask import Flask
from flask_peewee.db import Database

app = Flask(__name__)

# loads configuration
app.config.from_pyfile("app.cfg")
app.config.from_pyfile("app-dev.cfg", silent=True)

db = Database(app)

