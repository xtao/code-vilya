from peewee import *

from .card import Card
from .project import Project
from .basemodel import BaseModel

class Pull(BaseModel):
    card = ForeignKeyField(Card, related_name='pull')
    merged_at = DateTimeField(null=True)
    merged_commit_sha = CharField(max_length=40, null=True)
    origin_commit_sha = CharField(max_length=40, null=True)
    origin_project = IntegerField()
    origin_project_ref = CharField(max_length=1024)
    upstream_commit_sha = CharField(max_length=40, null=True)
    upstream_project = IntegerField()
    upstream_project_ref = CharField(max_length=1024)

    @property
    def can_close(self):
        return True
