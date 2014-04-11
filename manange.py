#!/usr/bin/env python

from flask.ext.script import Manager
from vilya.app import app
from scripts import register_commands

manager = Manager(app)
register_commands(manager)

if __name__ == "__main__":
    manager.run()
