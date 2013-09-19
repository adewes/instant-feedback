from functools import wraps,update_wrapper

from datetime import timedelta
from flask import request,make_response,abort,current_app
from models import Survey,User,Response
import pymongo
import settings
from settings import logger
import uuid

def crossdomain(origin=None, methods=None, headers=None,
                max_age=21600, attach_to_all=True,
                automatic_options=True):
    if methods is not None:
        methods = ', '.join(sorted(x.upper() for x in methods))
    if headers is not None and not isinstance(headers, basestring):
        headers = ', '.join(x.upper() for x in headers)
    if not isinstance(origin, basestring):
        origin = ', '.join(origin)
    if isinstance(max_age, timedelta):
        max_age = max_age.total_seconds()

    def get_methods():
        if methods is not None:
            return methods

        options_resp = current_app.make_default_options_response()
        return options_resp.headers['allow']

    def decorator(f):
        def wrapped_function(*args, **kwargs):
            if automatic_options and request.method == 'OPTIONS':
                resp = current_app.make_default_options_response()
            else:
                resp = f(*args, **kwargs)
                if isinstance(resp,str):
                    resp = make_response(resp)

            h = resp.headers

            h['Access-Control-Allow-Origin'] = origin
            h['Access-Control-Allow-Credentials'] = 'true'
            h['Access-Control-Allow-Methods'] = get_methods()
            h['Access-Control-Max-Age'] = str(max_age)
            h['P3P'] = 'CP="CURa ADMa DEVa PSAo PSDo OUR BUS UNI PUR INT DEM STA PRE COM NAV OTC NOI DSP COR"'
            if headers is not None:
                h['Access-Control-Allow-Headers'] = headers
            return resp

        f.provide_automatic_options = False
        return update_wrapper(wrapped_function, f)
    return decorator

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

def jsonp():
    
    def decorator(f):
        
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not 'callback' in request.args:
                abort(404)
            response = f(*args, **kwargs)
            if isinstance(response,str):
                response = make_response(response)
            response.data = "%s(%s)" % (request.args['callback'],response.data)
            response.mimetype = 'application/javascript'
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
            print request.user.document_id,str(request.survey['user'])
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
            if 'response_key' in request.args and request.args['response_key'] and request.survey['authorized_keys_only']:
                response_key = request.args['response_key']
                response = Response.collection.find_one({'survey_key' : request.survey['key'],'response_key':response_key},sort = [('_updated_at',pymongo.DESCENDING)])

                if response:
                    response['session'] = request.session
                    response.save()

            else:
                response_key = ''
                response = Response.collection.find_one({'survey_key' : request.survey['key'],'session':request.session},sort = [('_updated_at',pymongo.DESCENDING)])

            if not response:
                response = Response(**{'survey_key': request.survey['key'],'session':request.session,'response_key':response_key})

            request.response = response
            return f(*args, **kwargs)
        
        return decorated_function
    
    return decorator
