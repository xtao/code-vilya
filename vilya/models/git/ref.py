class GitRef(object):

    def __init__(self, repo, ref):
        self._repo = repo
        self._ref = ref

    def __unicode__(self):
        return u'%s:%s' (self._repo.path, self._ref)

    @property
    def files(self):
        pass

    @property
    def sha(self):
        return self._ref
