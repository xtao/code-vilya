from . import GitRepo


def clone(url, path, bare=False, **kwargs):
        # TODO: switch to `git clone` for higher speed. 
        repo = clone_repository(url, path, bare, **kwargs)
        return GitRepo(repo.path)
     
