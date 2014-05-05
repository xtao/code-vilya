
import os
import gzip
import shutil
from cStringIO import StringIO
from pygit2 import Repository, init_repository

class GitRepo(Repository):

    @classmethod
    def create(cls, path, bare=True):
        init_repository(path, bare=True)
        return cls.get(path=path)

    @classmethod
    def get(cls, path):
        if os.path.isdir(path):
            return cls(path=path)

    def get_obj(self, key):
        return super(GitRepo, self).get(key)

    def delete(self):
        if os.path.isdir(path):
            shutil.rmtree(path)

    def archive(self):
        content = self._jagare_repo.archive()
        outbuffer = StringIO()
        zipfile = gzip.GzipFile(mode='wb', compresslevel=6, fileobj=outbuffer)
        zipfile.writelines(content)
        zipfile.close()
        out = outbuffer.getvalue()

    def clone(self, ref_obj):
        pass

    @property
    def updated_at(self):
        commit = self.commits.get('HEAD')
        if not commit:
            return 0
        return int(commit.author_timestamp)

    @property
    def commits(self):
        pass

    @property
    def branches(self):
        pass

    @property
    def tags(self):
        pass

    @property
    def head(self):
        return self.commits.get('HEAD')

    @property
    def files(self):
        return self.head.files()

