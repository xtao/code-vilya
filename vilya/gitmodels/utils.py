# -*- coding: utf-8 -*-
from . import GitRepo
from pygit2 import clone_repository


def clone(url, path, bare=False, **kwargs):
        # TODO: switch to `git clone` for higher speed.
        repo = clone_repository(url, path, bare, **kwargs)
        return GitRepo(repo.path)
