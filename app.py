# -*- coding: utf-8 -*-

from vilya.middleware import DispatcherMiddleware
from vilya import frontend

app = frontend.create_app()
app.wsgi_app = DispatcherMiddleware(app)
