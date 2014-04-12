import re
import os

from threading import Lock
from wsgiauth.basic import BasicAuth
from werkzeug.exceptions import NotFound

from .app import app
from .libs.git_http_backend import assemble_WSGI_git_app
from .models.project import Project
from .models.user import User
from .models.permission import Permission, READ_PERM, WRITE_PERM



class DispatcherMiddleware(object):

    """Dispatch http request to flask app or git app"""

    def __init__(self, app):
        self.lock = Lock()
        self.config = app.config
        self.wsgi_app = app.wsgi_app
        self.realm = self.config.get('AUTH_REALM', 'Basic realm="Login Required"')
        self.git_root = os.path.abspath(app.config.get('GIT_ROOT', './repos'))
        self.httpauth = BasicAuth(self.realm, self.authenticate)
        self.git_app = None
        

    def get_project(self, environ):
        path = environ.get('PATH_INFO')
        match = re.match(r'^/(?P<owner_name>\w+)/(?P<project_name>\w+)(\.git)?(/.+)?', path)
        if match:
            owner_name = match.group('owner_name')
            project_name = match.group('project_name')
            return Project.select().where(
                    Project.owner_name==owner_name,
                    Project.name==project_name).get()

    def is_push(self, environ):
        path = environ.get('PATH_INFO')
        query_string = environ['QUERY_STRING']
        return ('service=git-receive-pack' in query_string or
               '/git-receive-pack' in environ['PATH_INFO']) 

    def authenticate(self, environ, username, password):
        project = self.get_project(environ)
        user = User.authenticate(username, password)
        perm = WRITE_PERM if self.is_push(environ) else READ_PERM
        if Permission.check_permission(project, user, perm):
            environ['GIT_PATH_INFO'] = os.path.join(self.git_root, project.path_info)
            return True
        return False

    def get_application(self, environ):
        user_agent = environ.get('HTTP_USER_AGENT')
        if user_agent and 'git' not in user_agent :
            return self.wsgi_app
        else:
            if environ.get('REMOTE_USER') is None:
                try:
                    res = self.httpauth(environ)
                except Project.DoesNotExist:
                    return NotFound()
                if not isinstance(res, basestring):
                    return res
                else:
                    environ['REMOTE_USER'] = res
                    environ['AUTH_TYPE'] = self.httpauth.authtype
            with self.lock:
                if not self.git_app:
                    self.git_app = assemble_WSGI_git_app(self.git_root)
                return self.git_app

    def __call__(self, environ, start_response):
        application = self.get_application(environ)
        return application(environ, start_response)

app.wsgi_app = DispatcherMiddleware(app)
