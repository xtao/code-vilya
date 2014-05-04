from pygit2 import (
        Object,
        Tree,
        TreeEntry,
        )
from pygit2 import (
        GIT_REF_SYMBOLIC,
        GIT_FILEMODE_BLOB,
        )

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


class InvalidProperty(Exception):

    def __init__(self, name, detail=''):
        self._name = name
        self._detail = detail

    def __unicode__(self):
        desc = u"Invalid Property '%s'"
        if self._detail:
            desc += '(%s)' % self._detail
        return desc


class Reference(ObjectProxy):

    def __init__(self, repo, obj):
        if obj.type == GIT_REF_SYMBOLIC:
            obj = obj.resolve()
        super(Reference, self).__init__(repo, obj)

    @property
    def commits(self):
        query = CommitQuery(self._repo, Commit)
        return query.where(ref=self.target)


class Branch(Reference):
    pass


class Tag(Reference):
    pass


class Commit(ObjectProxy):

    @property
    def files(self):
        query = FileQuery(self._repo, File)
        return query.where(commit=self._object)


class File(ObjectProxy):

    def __init__(self, repo, obj):
        if isinstance(obj, TreeEntry):
            obj = repo[obj.id]
        return super(File, self).__init__(repo, obj)

    @property
    def isdir(self):
        return isinstance(self._object, Tree)

    @property
    def isfile(self):
        return not self.isdir

    def listdir(self):
        return list(self)

    def create_file(self, name, data=''):
        if not name:
            raise InvalidProperty('name', 'is empty')
        if self.isdir:
            repo = self._repo
            blob_id = repo.create_blob(data)
            if blob_id:
                treebuilder = repo.TreeBuilder(self._object)
                treebuilder.insert(name, blob_id, GIT_FILEMODE_BLOB)
                oid = treebuilder.write()
                self._object = repo.get(oid)
                return repo.get(blob_id)

    def __iter__(self):
        if self.isdir:
            for entry in self._object:
                yield File(self._repo, entry)
        else:
            return []

    def __getitem__(self, key):
        if self.isdir:
            return File(self._repo, self._object[key])
