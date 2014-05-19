import os, uuid, random
from vilya.gitmodels.repo import GitRepo
from pygit2 import (
        Signature,
        GIT_FILEMODE_TREE,
        GIT_FILEMODE_BLOB,
        )


def create_repo(git_root, empty=True):
    repo = GitRepo.create(os.path.join(git_root, str(uuid.uuid1())))
    if not empty:
        fill_repo_data(repo)
    return repo

def random_file_line(length=64):
    char_range = range(32, 128)
    return ''.join(chr(random.choice(char_range)) for x in range(length))

def random_file_content(lines=10, line_len=64):
    return '\n'.join(random_file_line(line_len) for x in range(lines))

def create_tree(repo, structure=None):
    if not structure:
        structure = {
            'test_dir1':{
                'test_file1':random_file_content(),
                'test_file2':random_file_content(),
                },
            'test_dir2':{
                'test_file1':random_file_content(),
                'test_file2':random_file_content(),
                'test_file3':random_file_content(),
                'test_dir3':{
                    'dir_3_test_file1':random_file_content(),
                    'dir_3_test_file2':random_file_content(),
                    }
                },
            'test_file4':random_file_content(),
            'test_file5':random_file_content(),
            'test_file6':random_file_content(),
            'README.md':random_file_content(),
            }
    builder = repo.TreeBuilder()
    for k, v in structure.iteritems():
        if isinstance(v, dict):
            tree, _ = create_tree(repo, v)
            builder.insert(k, tree, GIT_FILEMODE_TREE)
        else:
            blob_id = repo.create_blob(v) 
            builder.insert(k, blob_id, GIT_FILEMODE_BLOB)
    return builder.write(), structure

def create_commit(repo, ref=None, author=None, email=None, msg='', tree=None, parents=None):
    author = author or 'testuser'
    email = email or ('%s@example.com' % author)
    sign = Signature(author, email)
    tree = tree or create_tree(repo)[0]
    parents = []
    ref = ref or 'HEAD'
    repo.create_commit(ref, sign, sign, msg, tree, parents)
    
def fill_repo_data(repo):
    pass
