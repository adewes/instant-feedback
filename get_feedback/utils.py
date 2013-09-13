from functools import wraps

from flask import request,make_response,abort
from models import Survey,User,Response
import settings
from settings import logger
import uuid

def _get_session():
    session = request.cookies.get('session')
    if not session:
        session = uuid.uuid4().hex
    return session

def _get_survey(survey_key):
    survey = Survey.collection.find_one({'key':survey_key})

    if not survey:
        abort(404)

    return survey

def with_session():
    
    def decorator(f):
        
        @wraps(f)
        def decorated_function(*args, **kwargs):
            request.session = _get_session()
            response = f(*args, **kwargs)
            if isinstance(response,str):
                response = make_response(response)
            response.set_cookie('session',request.session)
            return response
        
        return decorated_function
    
    return decorator

def with_user():
    
    def decorator(f):
        
        @wraps(f)
        def decorated_function(*args, **kwargs):
            user = User.collection.find_one({'session':request.session})
            if not user:
                user = User(session = request.session)
            request.user = user
            return f(*args, **kwargs)
        
        return decorated_function
    
    return decorator

def with_survey():
    
    def decorator(f):
        
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not 'survey_key' in kwargs:
                logger.debug("with_survey: No survey key given!")
                abort(404)
            request.survey = Survey.collection.find_one({'key':kwargs['survey_key']})
            if not request.survey:
                logger.debug("with_survey: Survey not found!")
                abort(404)
            return f(*args, **kwargs)
        
        return decorated_function
    
    return decorator

def with_field():
    
    def decorator(f):
        
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not 'field_type' in kwargs or not 'field_id' in kwargs or not hasattr(request,'survey'):
                abort(404)
            if not kwargs['field_type'] in settings.field_types:
                abort(403)
            if not request.survey.has_field(kwargs['field_type'],kwargs['field_id']):
                abort(404)
            request.field = request.survey.get_field(kwargs['field_type'],kwargs['field_id'])
            return f(*args, **kwargs)
        
        return decorated_function
    
    return decorator

def with_admin():
    def decorator(f):
        
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not hasattr(request,'survey') or not hasattr(request,'user'):
                logger.debug("with_admin: survey or user not loaded!")
                abort(404)
            if not request.survey['user'] == request.user:
                logger.debug("with_admin: not an admin!")
                abort(403)
            return f(*args, **kwargs)
        
        return decorated_function
    
    return decorator

def with_response():
    
    def decorator(f):
        
        @wraps(f)
        def decorated_function(*args, **kwargs):
            response = Response.collection.find_one({'survey_key' : request.survey['key'],'session':request.session})
            if not response:
                response = Response(**{'survey_key': request.survey['key'],'session':request.session})
            request.response = response
            return f(*args, **kwargs)
        
        return decorated_function
    
    return decorator
