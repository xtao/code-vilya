from pygit2 import Object, Tree, Blob
from pygit2 import GIT_REF_SYMBOLIC

from .query import (
        CommitQuery,
        BranchQuery,
        FileQuery,
        )

class ObjectProxy(object):

    def __init__(self, repo, obj):
        self._repo = repo
        self._object = obj

    def __getattr__(self, key):
        obj = getattr(self._object, key)
        if callable(obj):
            setattr(self, key) = obj
        return obj


class Reference(ObjectProxy):

    def __init__(self, repo, obj):
        if obj.type == GIT_REF_SYMBOLIC:
            obj = obj.resolve()
        super(Reference, self).__init__(repo, obj)

    @property
    def commits(self):
        query = CommitQuery(self._repo, Commit)
        return query.where(ref=self.target)


class Commit(ObjectProxy):

    @property
    def files(self):
        query = FileQuery(self._repo, File)
        return query.where(commit=self._object)


class File(ObjectProxy):

    @property
    def is_dir(self):
        return isinstance(self._object, Tree)

    @property
    def is_file(self):
        return not self.is_dir

    def list_dir(self):
        if self.is_dir:
            return list(self._object)
