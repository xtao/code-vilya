# -*- coding: utf-8 -*-

from flask.ext.cache import Cache
from flask_peewee.db import Database


db = Database()
cache = Cache()
