from peewee import *

from .basemodel import BaseModel
from .user import User
from .card import Card
from .pull import Pull
from .project import Project


class CardList(BaseModel):
    creator = ForeignKeyField(User, related_name='created_lists')
    project = ForeignKeyField(Project, related_name='lists')
    name = CharField(max_length=200)
    description = CharField(max_length=1024, null=True)
    number = IntegerField(index=True)
    order = IntegerField(index=True)
    role = IntegerField(
            default=0, 
            choices=[
                (0, 'normal'),
                (1, 'issues'),
                (2, 'pulls'),
                ])
    is_archived = BooleanField(null=True)
    archiver = ForeignKeyField(User)
    updated_at = DateTimeField()
    created_at = DateTimeField()

    @property
    def can_archive(self):
        if self.role == 0:
            return True
        return False

    @property
    def cards(self):
        return self.pulls or Card.select().where(Card.list_id==self.id)

    @property
    def pulls(self):
        if self.role==2:
            return Pull.select().where(Card.list_id==self.id)
        return []
