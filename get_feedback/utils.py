from functools import wraps

from flask import request,make_response

def _get_session():
    session = request.cookies.get('session')
    if not session:
        session = uuid.uuid4().hex
    return session

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