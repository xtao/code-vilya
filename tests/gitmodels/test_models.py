import os
from . import GitModelTestCase
from . import factory

class ModelTestCase(GitModelTestCase):

    def setUp(self):
        super(GitModelTestCase, self).setUp()
        self.repo = factory.create_repo(self._settings.GIT_REPO_ROOT)

    def tearDown(self):
        self.repo.delete()
        super(GitModelTestCase, self).tearDown()

    def test_repo_exists(self):
        assert os.path.isdir(self.repo.path)

    def test_commits(self):
        repo = self.repo
        # test empty commit
        commits = list(repo.commits)
        assert len(commits)==0

        # test add commit
        tree, _ = factory.create_tree(repo)
        repo.commits.create('HEAD', None, 'testuser', 'test@example.com', 'initial commit', tree)
        commits = list(repo.commits)
        assert len(commits)==1

        # test commit information
        commit = commits[0]
        assert commit.message=='initial commit'
        assert commit.author.name=='testuser'
        assert commit.author.email=='test@example.com'
        assert commit.tree.oid == tree

