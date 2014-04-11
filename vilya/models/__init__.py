def register_admin(admin):
    from .card import Card
    from .cardlist import CardList
    from .counter import Counter
    from .project import Project
    from .pull import Pull
    from .user import User, UserAdmin
    from .team import Team

    admin.register(Card)
    admin.register(CardList)
    admin.register(Project)
    admin.register(Team)
    admin.register(User, UserAdmin)
