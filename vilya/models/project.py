from peewee import *

from .basemodel import BaseModel
from .user import User
from .counter import Counter

class Project(BaseModel):
    creator = ForeignKeyField(User)
    ancestor = ForeignKeyField('self', null=True)
    owner_name = CharField()
    name = CharField(max_length=200)
    description = CharField(max_length=1024, null=True)
    upstream = IntegerField(null=True)
    counter = ForeignKeyField(Counter, null=True)
    created_at = DateTimeField()
    updated_at = DateTimeField()

