# -*- coding: utf-8 -*-
import re
from pygit2 import (
    GIT_SORT_TOPOLOGICAL,
    GIT_SORT_TIME,
    GIT_BRANCH_LOCAL,
    GIT_BRANCH_REMOTE
)
from pygit2 import (
    Tree,
    Signature,
)


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
        raw_obj = self.where(**kwargs)._get()
        return self._cls(self._repo, raw_obj) if raw_obj else None

    def all(self, **kwargs):
        iterator = self.where(**kwargs)._all()
        for obj in iterator:
            if obj:
                yield self._cls(self._repo, obj)

    def count(self):
        return len(list(self._all()))

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
        return self

    def _qname(self, name):
        escaped = re.sub(r'[^a-zA-Z0-9]+', '_', name)
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

    def __len__(self):
        return self.count()

    def __bool__(self):
        return bool(self.count())


class BranchQuery(Query):

    @property
    def filter(self):
        filter_ = 0
        if self.remote:
            filter_ |= GIT_BRANCH_REMOTE
        if self.local or filter_ == 0:
            filter_ |= GIT_BRANCH_LOCAL
        return filter_

    def _all(self):
        repo = self._repo
        filter_ = self.filter
        branches = repo.listall_branches(filter_)
        for branch in branches:
            yield repo.lookup_branch(branch)

    def _get(self):
        repo = self._repo
        return repo.lookup_branch(self.name, self.filter)

    def create(self, name, commit, force=False):
        repo = self._repo
        if repo.create_branch(name, commit._object, force):
            return self._cls(repo, repo.lookup_branch(name))


class CommitQuery(Query):

    def _all(self):
        if self._repo.is_empty:
            return
        from_id = self.from_id or self._repo.head.oid
        order_by = self.order or GIT_SORT_TOPOLOGICAL
        walker = self._repo.walk(from_id, order_by)
        count = 0
        limit_count = self.limit_count or 0
        skip_count = self.skip_count or 0
        for commit in walker:
            if count >= self.skip_count:
                yield commit
            count += 1
            if limit_count > 0 and count >= limit_count + skip_count:
                return

    def _get(self):
        if self.ref:
            repo = self._repo
            try:
                return repo.revparse_single(unicode(self.ref))
            except KeyError as e:
                return None
        else:
            res = list(self.limit(1).all())
            return res[0] if res else None

    def create(self, ref, parent_commit, author, email, message, tree):
        repo = self._repo
        committer = Signature(author, email)
        p_commits = [unicode(parent_commit), ] if parent_commit else []
        oid = repo.create_commit(
            unicode(ref),
            committer, committer,
            message,
            tree,
            p_commits)
        return self._cls(repo, repo[oid])

    @property
    def last(self):
        return self.limit(1).get()


class TagQuery(Query):

    def _all(self):
        repo = self._repo
        refs = repo.listall_references()
        for ref in refs:
            if ref.startswith("refs/tags/"):
                yield repo.lookup_reference(ref)

    def _get(self):
        repo = self._repo
        try:
            return repo.lookup_reference("refs/tags/" + self.name)
        except KeyError as e:
            return None

    def create(self, name, obj, tagger_name, email,  message):
        oid = obj.oid
        type_ = obj.type
        repo = self._repo
        tagger = Signature(tagger_name, email)
        tag_oid = repo.create_tag(name, oid, type_, tagger, message)
        return self._cls(repo, repo[tag_oid])


class FileQuery(Query):

    def _all(self):
        f = self._get()
        if f:
            return list(f)
        else:
            return []

    def _get(self):
        path = self.path or ''
        commit = self.commit
        tree = commit.tree
        if not path:
            return tree
        else:
            try:
                return tree[path]
            except KeyError as e:
                return None

    @property
    def root(self):
        return self.get(path='')
