import os
import nose

from flask.ext.script import Command

class RunTests(Command):
    
    def run(self):
        config = nose.config.Config()
        config.configureWhere(os.path.abspath(os.path.curdir))
        nose.main()
