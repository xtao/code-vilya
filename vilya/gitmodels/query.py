import re
import os
from .objects import ObjectProxy
from pygit2 import GIT_SORT_TOPOLOGICAL, GIT_BRANCH_LOCAL, GIT_BRANCH_REMOTE
from pygit2 import Tree

class QueryKeyNotAccepted(Exception):
    def __init__(self, key):
        self._key = key

    def __unicode__(self):
        return u"Query key not accepted: %s" % self._key
        

class Query(object):

    __accept_query__ = None

    def __init__(self, repo, cls):
        self._repo = repo
        self._cls = cls

    def get(self, **kwargs):
        raw_obj = self._get()
        return self._cls(self._repo, raw_obj) if raw_obj else None

    def all(self, **kwargs):
        iterator = self.where(**kwargs)._all()
        for obj in iterator:
            if obj:
                yield self._cls(self._repo, obj)

    def where(self, **kwargs):
        for k, v in kwargs.iteritems():
            self._setq(k, v)
        return self

    def order_by(self, order_by):
        self._setq = ('order', order_by)
        return self

    def limit(self, number):
        self._setq('limit_count', number)
        return self

    def skip(self, number):
        self._setq('skip_count', number)
        return skip

    def _qname(self, name):
        escaped = re.sub(r'[^a-zA-Z0-9]+','_',name)
        return ('_ref_query_%s' % escaped)

    def _setq(self, key, value):
        if self.__accept_query__ is not None:
            if value not in self.__accept_query__:
                raise QueryKeyNotAccepted(key)
        qname = self._qname(key)
        setattr(self, qname, value)

    def _getq(self, key):
        qname = self._qname(key) 
        if hasattr(self, qname):
            return getattr(self, qname)

    def _get(self, **kwargs):
        obj_list = list(self.where(**kwargs).limit(1).all())
        if obj_list:
            return obj_list[0]

    def _all(self, **kwargs):
        raise NotImplementedError

    def __iter__(self):
        return self.all()

    def __getattr__(self, key):
        if key.startswith('_'):
            return super(Query, self).__getattr__(key)
        return self._getq(key)


class BranchQuery(Query):

    @property
    def filter(self):
        filter_ = 0
        if self.remote:
            filter_ |= GIT_BRANCH_REMOTE
        if self.local or filter_==0:
            filter_ |= GIT_BRANCH_LOCAL

    def _all(self):
        repo = self._repo
        filter_ = self.filter
        branches = repo.listall_branches(filter_)
        for branch in branches:
            yield repo.lookup_branch(filter_)

    def _get(self):
        repo = self._repo
        return repo.lookup_branch(self.name, self.filter)

    def create(self, name, commit, force=False):
        repo = self._repo
        if repo.create_branch(name, commit, force)
            return Branch(repo, repo.lookup_branch(name))


class CommitQuery(Query):

    def _all(self):
        from_id = self.from_id or self._repo.head.target
        order_by = self.order or GIT_SORT_TOPOLOGICAL
        walker =  self._repo.walk(from_id, order)
        count = 0
        for commit in walker:
            if count >= self.skip_count:
                yield commit
            count +=1
            if self.limit and count >= self.limit:
                break

    def _get(self):
        repo = self.repo
        return  repo.revparse_single(self.ref)

class TagQuery(Query):
    
    def _all(self):
        repo = self._repo
        refs = repo.listall_references()
        for ref in refs:
            if ref.startswith("refs/tags/"):
                yield repo.lookup_reference(ref)

    def _get(self):
        repo = self._repo
        return repo.lookup_reference("refs/tags/" + self.name)

    def create(self, name, commit, tagger, message):
        oid = commit.id
        repo = self._repo
        tag_oid = repo.create_tag(name, oid, tagger, message)
        return Tag(repo, repo.get(tag_oid))


class FileQuery(Query):

    def _all(self):
        path = self.path or ''
        commit = self.commit
        tree = commit.tree
        path_components = path.split(os.path.sep)
        for component in path_components:
            if not component: continue
            tree_entry = tree.get(component)
            if tree_entry:
                obj = tree[tree_entry.id]
                if isinstance(obj, Tree):
                    tree = obj
                elif component == path_components[-1]:
                    return [obj, ]
                else:
                    return []
        return [tree, ]

    def _get(self):
        obj = self._all()
        return obj[0] if obj else None

    @property
    def root(self):
        return self.get(path='')
