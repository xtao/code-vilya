# -*- coding: utf-8 -*-

from functools import wraps
from flask_peewee.admin import Admin
from .. import factory
from ..core import auth
from ..models import register_admin


def create_app(settings_override=None):
    app = factory.create_app(__name__, __path__, settings_override)

    admin = Admin(app, auth)
    register_admin(admin)
    admin.setup()
    return app


def route(bp, *args, **kwargs):
    def decorator(f):
        @bp.route(*args, **kwargs)
        @wraps(f)
        def wrapper(*args, **kwargs):
            return f(*args, **kwargs)
        return f

    return decorator
