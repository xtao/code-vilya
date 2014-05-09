# -*- coding: utf-8 -*-

from flask.ext.cache import Cache
from flask_peewee.db import Database
from .auth import Auth


db = Database()
cache = Cache()
auth = Auth()
