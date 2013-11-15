import mongobean.orm as orm

import settings

orm.default_db = settings.db

class Response(orm.Document):
    pass

class User(orm.Document):

    def is_admin(self,survey):
        if survey['user'] == self:
            return True
        return False

class Survey(orm.Document):

    def has_field(self,field_type,field_id):
        if not field_type in self['fields'] or not field_id in self['fields'][field_type]:
            return False
        return True

    def get_field(self,field_type,field_id):
        if not field_type in settings.field_types:
            raise AttributeError("Invalid field type: %s!" % field_type)
        if not self.has_field(field_type,field_id):
            raise AttributeError("field of type %s and ID %s not found!" % (field_type,field_id) )
        return settings.field_types[field_type](self['fields'][field_type][field_id])

    def init_field(self,field_type,field_id):
        field = settings.field_types[field_type]()
        self.set_field(field_type,field_id,field)
        return field

    def set_field(self,field_type,field_id,field):
        if not field_type in self['fields']:
            self['fields'][field_type] = {} 
        self['fields'][field_type][field_id] = field.attributes
