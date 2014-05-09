from peewee import *
from datetime import datetime
from ..core import db

class BaseModel(db.Model):

    @classmethod
    def update(cls, *args, **kwargs):
        if hasattr(cls, 'updated_at'):
            now = datetime.now()
            kwargs['updated_at'] = now
        return super(BaseModel, cls).update(*args, **kwargs)

    @property
    def anonymous_perm(self):
        return 1

    @property
    def perm_name(self):
        return str(self.__class__.__name__).lower()

    def pre_save(self, is_create):
        now = datetime.now()
        if hasattr(self, 'updated_at'):
            self.updated_at = now
        if is_create and hasattr(self, 'created_at'):
            self.created_at = now

    def post_save(self, created):
        pass

    def save(self, *args, **kwargs):
        created = not bool(self.get_id())
        self.pre_save(created)
        super(BaseModel, self).save()
        self.post_save(created)

    def pre_delete(self):
        pass

    def post_delete(self):
        pass

    def delete_instance(self, *args, **kwargs):
        self.pre_delete()
        super(BaseModel, self).delete_instance(*args, **kwargs)
        self.post_delete()
