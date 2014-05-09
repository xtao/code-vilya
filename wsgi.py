# -*- coding: utf-8 -*-

from werkzeug.serving import run_simple
from werkzeug.wsgi import DispatcherMiddleware

from vilya import frontend, api
from vilya.middleware import DispatcherMiddleware as GitDispatcherMiddleware

frontend_app = frontend.create_app()
frontend_app.wsgi_app = DispatcherMiddleware(frontend_app, {'/api':api.create_app()})
frontend_app.wsgi_app = GitDispatcherMiddleware(frontend_app)

application = frontend_app

if __name__ == "__main__":
    run_simple('localhost', 5000, application, use_reloader=True, use_debugger=True)
