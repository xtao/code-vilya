# -*- coding: utf-8 -*-

import os


def init_app(app):
    repo_root = app.config['GIT_REPO_ROOT']
    temp_repo_root = app.config['GIT_TEMP_REPO_ROOT']
    if not os.path.isdir(repo_root):
        os.mkdir(repo_root)
    if not os.path.isdir(temp_repo_root):
        os.mkdir(temp_repo_root)
