import os, shutil

from unittest import TestCase

from tests import settings
from vilya import gitmodels


class VilyaTestCase(TestCase):

    def _init_git_env(self):
        if not os.path.isdir(settings.GIT_REPO_ROOT):
            os.mkdir(settings.GIT_REPO_ROOT)
        if not os.path.isdir(settings.GIT_TEMP_REPO_ROOT):
            os.mkdir(settings.GIT_TEMP_REPO_ROOT)

    def _clear_git_env(self):
        if os.path.isdir(settings.GIT_REPO_ROOT):
            shutil.rmtree(settings.GIT_REPO_ROOT)
        if os.path.isdir(settings.GIT_TEMP_REPO_ROOT):
            shutil.rmtree(settings.GIT_TEMP_REPO_ROOT)

    def setUp(self):
        super(VilyaTestCase, self).setUp()
        self._init_git_env()

    def tearDown(self):
        self._clear_git_env()
        super(VilyaTestCase, self).tearDown()


class VilyaAppTestCase(VilyaTestCase):

    def _create_app(self, settings):
        raise NotImplementedError

    def _create_fixtures(self):
        pass

    def setUp(self):
        super(VilyaAppTestCase, self).setUp()
        self.app = self._create_app(settings)
        self.client = self.app.test_client()
        self.app_context = self.app.app_context()
        self.app_context.push()
        self._create_fixtures()

    def tearDown(self):
        self.app_context.pop()
        super(VilyaAppTestCase, self).tearDown()


