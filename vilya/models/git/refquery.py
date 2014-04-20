import re

class QueryKeyNotAccepted(Exception):
    def __init__(self, key):
        self._key = key

    def __unicode__(self):
        return u"Query key not accepted: %s" % self._key
        

class RefQuery(object):

    __accept_query__ = None

    def __init__(self, cls):
        self._cls = cls

    def get(self, **kwargs):
        return self.where(**kwargs)._get()

    def get_list(self, **kwargs):
        return self.where(**kwargs)._get_list()

    def where(self, **kwargs):
        for k, v in kwargs.iteritems():
            self._setq(k, v)
        return self

    def limit(self, number):
        self._limit = number
        return self

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

    def _get(self):
        objs = self.where(limit=1)._get_list()
        if len(objs):
            return objs[0]

    def _get_list(self):
        raise NotImplementedError('This method need to be override')

    def __iter__(self):
        return self._get_list()

    def __getattr__(self, key):
        return self._getq(key)


class BranchQuery(RefQuery):

    def _get_list(self):
        repo = self.repo
        if repo:
            branches = repo.branches
            if self.limit:
                return branches[:self.limit]
            return branches
