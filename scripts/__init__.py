def register_commands(manager):
    from .admin import CreateSuperUser
    manager.add_command('createsuperuser', CreateSuperUser)
