import mongobean.orm as orm

import settings

orm.default_db = settings.db

class Response(orm.Document):
    pass

class User(orm.Document):
    pass

class Survey(orm.Document):
    pass