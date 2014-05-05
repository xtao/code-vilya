#!/usr/bin/env python

from flask.ext.script import Manager
from scripts import register_commands
from wsgi import application

manager = Manager(application)
register_commands(manager)

if __name__ == "__main__":
    manager.run()
