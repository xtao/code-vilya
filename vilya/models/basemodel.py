from peewee import *
from ..app import db
from datetime import datetime


class BaseModel(db.Model):

    @classmethod
    def update(cls, *args, **kwargs):
        if hasattr(cls, 'updated_at') and isinstance(cls.updated_at, DateTimeField):
            now = datetime.now()
            kwargs['updated_at'] = now
        return super(BaseModel, cls).update(*args, **kwargs)

    @classmethod
    def create(cls, *args, **kwargs):
        now = datetime.now()
        if hasattr(cls, 'updated_at') and isinstance(cls.updated_at, DateTimeField):
            kwargs['updated_at'] = now
        if hasattr(cls, 'created_at') and isinstance(cls.created_at, DateTimeField):
            kwargs['created_at'] = now
        return super(BaseModel, cls).create(*args, **kwargs)

