# -*- coding: utf-8 -*-

import re
import os

from threading import Lock
from wsgiauth.basic import BasicAuth
from werkzeug import url_decode
from werkzeug.exceptions import NotFound

from .libs.git_http_backend import assemble_WSGI_git_app


class DispatcherMiddleware(object):

    """Dispatch http request to flask app or git app"""

    def __init__(self, app):
        self.lock = Lock()
        self.config = app.config
        self.wsgi_app = app.wsgi_app
        self.realm = self.config.get('AUTH_REALM',
                                     'Basic realm="Login Required"')
        self.git_root = os.path.abspath(app.config.get('GIT_ROOT', './repos'))
        self.httpauth = BasicAuth(self.realm, self.authenticate)
        self.git_app = None

    def get_project(self, environ):
        from .models.project import Project
        path = environ.get('PATH_INFO')
        match = re.match(r'^/(?P<owner_name>\w+)/(?P<project_name>\w+)(\.git)?(/.+)?', path)
        if match:
            owner_name = match.group('owner_name')
            project_name = match.group('project_name')
            return Project.select().where(
                Project.owner_name == owner_name,
                Project.name == project_name).get()

    def is_push(self, environ):
        path = environ.get('PATH_INFO')
        query_string = environ['QUERY_STRING']
        return ('service=git-receive-pack' in query_string or
                '/git-receive-pack' in environ['PATH_INFO'])

    def authenticate(self, environ, username, password):
        from .models.user import User
        from .models.permission import Permission, READ_PERM, WRITE_PERM
        project = self.get_project(environ)
        user = User.authenticate(username, password)
        perm = WRITE_PERM if self.is_push(environ) else READ_PERM
        if Permission.check_permission(project, user, perm):
            environ['GIT_PATH_INFO'] = os.path.join(self.git_root, project.path_info)
            return True
        return False

    def get_application(self, environ):
        user_agent = environ.get('HTTP_USER_AGENT')
        if user_agent and 'git' not in user_agent:
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


class HTTPMethodOverrideMiddleware(object):
    """The HTTPMethodOverrideMiddleware middleware implements the hidden HTTP
    method technique. Not all web browsers support every HTTP method, such as
    DELETE and PUT. This middleware class allows clients to provide a method
    override parameter via an HTTP header value or a querystring parameter. This
    middleware will look for the header paramter first followed by the
    querystring. The default HTTP header name is `X-HTTP-METHOD-OVERRIDE` and
    the default querystring parameter name is `__METHOD__`. These can be changed
    via the constructor parameters `header_name` and `querystring_param`
    respectively. Additionally, a list of allowed HTTP methods may be specified
    via the `allowed_methods` constructor parameter. The default allowed methods
    are GET, HEAD, POST, DELETE, PUT, PATCH, and OPTIONS.
    """

    bodyless_methods = frozenset(['GET', 'HEAD', 'OPTIONS', 'DELETE'])

    def __init__(self, app, header_name=None,
                 querystring_param=None, allowed_methods=None):
        header_name = header_name or 'X-HTTP-METHOD-OVERRIDE'

        self.app = app
        self.header_name = 'HTTP_' + header_name.replace('-', '_')
        self.querystring_param = querystring_param or '__METHOD__'
        self.allowed_methods = frozenset(allowed_methods or
            ['GET', 'HEAD', 'POST', 'DELETE', 'PUT', 'PATCH', 'OPTIONS'])

    def _get_from_querystring(self, environ):
        if self.querystring_param in environ.get('QUERY_STRING', ''):
            args = url_decode(environ['QUERY_STRING'])
            return args.get(self.querystring_param)
        return None

    def _get_method_override(self, environ):
        return environ.get(self.header_name, None) or \
               self._get_from_querystring(environ) or ''

    def __call__(self, environ, start_response):
        method = self._get_method_override(environ).upper()

        if method in self.allowed_methods:
            method = method.encode('ascii', 'replace')
            environ['REQUEST_METHOD'] = method

        if method in self.bodyless_methods:
            environ['CONTENT_LENGTH'] = '0'

        return self.app(environ, start_response)
