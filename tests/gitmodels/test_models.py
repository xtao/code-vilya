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

    def test_commits(self):
        repo = self.repo
        # test empty commit
        commits = list(repo.commits)
        assert len(commits) == 0

        # test add commit
        tree, _ = factory.create_tree(repo)
        repo.commits.create('HEAD', None, 'testuser', 'test@example.com', 'initial commit', tree)
        commits = list(repo.commits)
        assert len(commits) == 1

        # test commit information
        commit = commits[0]
        assert commit.message == 'initial commit'
        assert commit.author.name == 'testuser'
        assert commit.author.email == 'test@example.com'
        assert commit.tree.oid == tree

        # add several commits
        commit_list = [commit, ]
        for i in range(10):
            name = 'testuser%s' % i
            email = 'test%s@example.com' % i
            message = 'commit %s' % (i+2)
            commit = repo.commits.create('HEAD', commit, name, email, message, tree)
            commit_list.append(commit)

        commits = list(repo.commits)
        assert len(commits)==11

        # test commits query
        for c in commit_list:
            commit = repo.commits.get(ref=c)
            assert commit.message == c.message
            assert commit.author.name == c.author.name
            assert commit.author.email == c.author.email
            assert commit.oid == c.oid

        count = 0
        for i, commit in enumerate(repo.commits.limit(5).all(), 1):
            c = commit_list[-i]
            count += 1
            assert commit.oid == c.oid
        assert count == 5

        count = 0
        for i, commit in enumerate(repo.commits.limit(5).skip(3).all(), 1):
            c = commit_list[-i-3]
            count += 1
            assert commit.oid == c.oid
        assert count == 5

        count = 0

        for i, commit in enumerate(repo.commits.limit(5).skip(8).all(), 1):
            c = commit_list[-i-8]
            count += 1
            assert commit.oid == c.oid
        assert count == 3

    def test_branches(self):
        repo = self.repo
        commits = list(repo.commits)
        assert len(commits) == 0

        branches = list(repo.branches.all())
        assert len(branches) == 0

        factory.create_commit(repo)
        commits = list(repo.commits)
        assert len(commits) == 1
        commit = commits[0]

        branches = list(repo.branches.all())
        assert len(branches) == 1

        # create branch
        repo.branches.create('test_branch', commit)
        branches = list(repo.branches.all())
        assert len(branches) == 2

        # find branch
        branch = repo.branches.get(name='test_branch')
        assert branch.shorthand == 'test_branch'
        assert not branch.is_head()

        # rename branch
        branch.rename('test_branch_renamed')
        branch = repo.branches.get(name='test_branch')
        assert branch == None
        branch = repo.branches.get(name='test_branch_renamed')
        assert branch.shorthand == 'test_branch_renamed'

        # add commit
        commits = list(branch.commits.all())
        assert len(commits) == 1

        master = repo.branches.get(name='master')
        for i in range(5):
            tree, _ = factory.create_tree(repo)
            master.add_commit(
                    'testuser%s' % i,
                    'test%s@test.com' % i,
                    'commit master %s' % i,
                    tree)
        assert len(master.commits) == 6


        branch = repo.branches.get(name='test_branch_renamed')
        commit_list = commits
        for i in range(5):
            tree, _ = factory.create_tree(repo)
            commit = branch.add_commit(
                    'testuser%s' % i,
                    'test%s@test.com' % i,
                    'commit test%s' % i,
                    tree)
            commit_list.append(commit)

        assert len(commits) == 6

        commits = list(branch.commits.all())
        for i, commit in enumerate(commits,1):
            c = commit_list[-i]
            assert c.hex == commit.hex

        branch.delete()
        assert len(repo.branches) == 1


    def test_tags(self):
        repo = self.repo

        factory.create_commit(repo)
        master = repo.branches.get(name='master')
        tree, _ = factory.create_tree(repo)
        for i in range(10):
            master.add_commit(
                    'testuser%s' % i,
                    'test%s@test.com' % i,
                    'commit master %s' % i,
                    tree)

        # add tags
        commits = list(master.commits)

        for i in range(0, 9, 2):
            repo.tags.create('v0.%d' % i, commits[i], 'testtagger', 'test@test.com', 'tag message')
            assert len(repo.tags) == (i/2 + 1)

        # query tags
        for i in range(0, 9, 2):
            name = 'v0.%d' % i
            tag = repo.tags.get(name=name)
            assert tag
            assert tag.get_object().hex == commits[i].hex

        # delete tags
        for i in range(0, 9, 2):
            name = 'v0.%d' % i
            tag = repo.tags.get(name=name)
            tag.delete()
            tag = repo.tags.get(name=name)
            assert tag == None
            assert len(repo.tags) == 5 - (i/2 + 1)
            
    def test_files(self):
        repo = self.repo
        tree, structure = factory.create_tree(repo)
        factory.create_commit(repo, tree=tree)

        files = repo.files
        def walk_structure(name, value, path):
            path = os.path.join(path, name)
            f = files.get(path=path)
            if isinstance(value, dict):
                assert f.isdir()
                assert not f.isfile()
                # test list dir
                dirs = f.listdir()
                file_names = [f.name for f in dirs]
                for k, v in value.iteritems():
                    walk_structure(k, v, path)
            else:
                assert f.isfile()
                assert not f.isdir()
                # test file content
                assert f.data == value

        walk_structure('', structure, '')

        # test unexists paths
        f = files.get(path='some/unexists/path')
        assert not f
