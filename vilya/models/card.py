from peewee import *

from .basemodel import BaseModel
from .user import User


class Card(BaseModel):
    list_id = IntegerField()
    creator = ForeignKeyField(User, related_name='cards')
    name = CharField(max_length=200)
    description = TextField(null=True)
    number = IntegerField()
    order = IntegerField()
    is_archived = BooleanField(default=False)
    archiver = ForeignKeyField(User, related_name='archived_cards')
    closed_at = DateTimeField(null=True)
    closer = ForeignKeyField(User, related_name='closed_cards')
    created_at = DateTimeField()
    updated_at = DateTimeField()

    @property
    def can_close(self):
        return False

    def __unicode__(self):
        return u'#%d %s'  % (self.number, name)


