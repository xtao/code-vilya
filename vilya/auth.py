from flask_peewee.auth import Auth as FPAuth



class Auth(FPAuth):

    def get_user_model(self):
        from vilya.models.user import User
        return User

    def get_model_admin(self):
        from vilya.models.user import UserAdmin
        return UserAdmin
