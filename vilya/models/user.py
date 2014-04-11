from peewee import *

from flask_peewee.auth import BaseUser
from .basemodel import BaseModel

class User(BaseModel, BaseUser):
    username = CharField(unique=True)
    password = CharField()
    email = CharField(index=True)
    is_super_user = BooleanField()

