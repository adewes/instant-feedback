from flask import Flask,render_template,request,make_response,redirect,url_for,abort

import settings
import uuid
import json
import time
from collections import defaultdict
from models import Survey,User,Response
from utils import with_session
from functools import wraps

app = Flask(__name__)

def valid_survey():
    
    def decorator(f):
        
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not 'survey_key' in kwargs:
                abort(404)
            request.survey = _get_survey(kwargs['survey_key'])
            return f(*args, **kwargs)
        
        return decorated_function
    
    return decorator

def valid_admin():
    def decorator(f):
        
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not 'admin_key' in kwargs:
                abort(403)
            survey = Survey.collection.find_one({'admin_key':kwargs['admin_key']})
            if not survey:
                abort(403)
            request.survey = survey
            return f(*args, **kwargs)
        
        return decorated_function
    
    return decorator

def with_response():
    
    def decorator(f):
        
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'session_key' in request.args:
                session_key = request.args['session_key']
            else:
                session_key = request.session
            print "Session key:",session_key
            response = Response.collection.find_one({'survey_key' : request.survey['key'],'session':session_key})
            if not response:
                response = Response(**{'survey_key': request.survey['key'],'session':session_key})
            request.response = response
            return f(*args, **kwargs)
        
        return decorated_function
    
    return decorator

def _get_survey(survey_key):
    survey = Survey.collection.find_one({'key':survey_key})

    if not survey:
        abort(404)

    return survey

def _get_summary(survey):

    responses = list(Response.collection.find({'survey_key' : survey['key']}))

    if not len(responses):
        abort(404)

    summary = {}

    for key in settings.feature_types:
        aggregator = settings.feature_types[key]['aggregator']
        summary[key] = aggregator(responses)
    return summary

@app.route('/')
@with_session()
def welcome():
    context = {'session' : request.session}
    response = make_response(render_template("welcome.html",**context))
    return response

@app.route('/index')
@with_session()
def index():
    surveys = Survey.collection.find({'session':request.session})
    context = {'surveys':surveys}
    response = make_response(render_template("survey/index.html",**context))
    return response

@app.route('/details/<admin_key>')
@with_session()
def details(admin_key):
    survey = Survey.collection.find_one({'admin_key':admin_key})
    responses = Response.collection.find({'survey_key': survey['key']}).count()
    if not survey:
        abort(404)
    context = {'survey':survey,'responses':responses}
    response = make_response(render_template("survey/details.html",**context))

    return response

@app.route('/toogle_authorized_keys_only/<admin_key>')
@with_session()
@valid_admin()
def toggle_authorized_keys_only(admin_key):

    if not 'authorized_keys_only' in request.survey:
        request.survey['authorized_keys_only'] = True

    request.survey['authorized_keys_only'] = not request.survey['authorized_keys_only']
    request.survey.save()
    return redirect(url_for("details",admin_key = request.survey['admin_key']))

@app.route('/clear_authorized_keys/<admin_key>')
@with_session()
@valid_admin()
def clear_authorized_keys(admin_key):
    request.survey['authorized_keys'] = []
    request.survey.save()
    return redirect(url_for("details",admin_key = request.survey['admin_key']))

@app.route('/new',methods = ['GET','POST'])
@with_session()
def new():

    context = {}

    if request.method == 'POST':
        survey = Survey(authorized_keys = [],authorized_keys_only = False,key = uuid.uuid4().hex,name = request.form['name'],admin_key = uuid.uuid4().hex,session = request.session)
        survey.save()
        return redirect(url_for("details",admin_key = survey['admin_key']))
    else:
        response = make_response(render_template("survey/new.html",**context))

    return response

def request_wants_json():
    best = request.accept_mimetypes \
        .best_match(['application/json', 'text/html'])
    return best == 'application/json' and \
        request.accept_mimetypes[best] > \
        request.accept_mimetypes['text/html']

@app.route('/authorize_session_key/<admin_key>',methods = ['GET'])
@with_session()
@valid_admin()
def authorize_session_key(admin_key):

    if not "session_key" in request.args:
        return json.dumps({'status':404,'message' : 'session_key parameter is missing!'})

    session_key = request.args["session_key"]
    
    if not 'authorized_keys' in request.survey:
        request.survey['authorized_keys'] = []
    if not session_key in request.survey['authorized_keys']:
        request.survey['authorized_keys'].append(session_key)

    request.survey.save()
    if request_wants_json():
        return json.dumps({'status':200})
    else:
        return redirect(url_for("details",admin_key = request.survey['admin_key']))

@app.route('/remove_session_key/<admin_key>',methods = ['GET'])
@with_session()
@valid_admin()
def remove_session_key(admin_key):

    if not "session_key" in request.args:
        return json.dumps({'status':404,'message' : 'session_key parameter is missing!'})

    session_key = request.args["session_key"]

    if not 'authorized_keys' in request.survey or not session_key in request.survey['authorized_keys']:
        return json.dumps({'status':404,'message' : 'session_key %s not in list of authorized_keys!' % session_key})

    request.survey['authorized_keys'].remove(session_key)
    request.survey.save()

    if request_wants_json():
        return json.dumps({'status':200})
    else:
        return redirect(url_for("details",admin_key = request.survey['admin_key']))

@app.route('/update_response/<survey_key>/<feature_type>/<feature_id>',methods = ['GET','POST'])
@with_session()
@valid_survey()
@with_response()
def update_response(survey_key,feature_type,feature_id):

    if request.survey['authorized_keys_only'] and not request.response['session'] in request.survey['authorized_keys']:
        return json.dumps({'status':403,'html': ''})

    if request.method == 'POST':
        if not "value" in request.form:
            abort(500)
        value = request.form["value"]
    elif request.method == 'GET':
        if not "value" in request.args:
            abort(500)
        value = request.args["value"]
    if not feature_type in settings.feature_types:
        abort(500)
    feature_settings = settings.feature_types[feature_type]
    parser = feature_settings['parser']
    template =feature_settings['template']
    parsed_value = parser(value)

    if not feature_type in request.response:
        request.response[feature_type] = {}
    request.response[feature_type][feature_id] = parsed_value
    request.response.save()
    value = request.response[feature_type][feature_id]

    return json.dumps({'status':200,'html':render_template(template,**{'id' : feature_id,'value' : value})})
    
@app.route('/get_html/<survey_key>/<feature_type>/<feature_id>',methods = ['GET'])
@with_session()
@valid_survey()
@with_response()
def get_html(survey_key,feature_type,feature_id):
    
    feature_settings = settings.feature_types[feature_type]
    template =feature_settings['template']

    if 'admin_key' in request.args and request.args['admin_key'] == request.survey['admin_key']:
        admin = True
        summary = _get_summary(request.survey)
        if not feature_type in summary or not feature_id in summary[feature_type]:
            abort(404)
        return json.dumps({'status':200,'html':render_template(template,**{'summary':summary[feature_type][feature_id],'admin':True,'id' : feature_id})})
    else:
        if request.survey['authorized_keys_only'] and not request.response['session'] in request.survey['authorized_keys']:
            return json.dumps({'status':403,'html': ''})
        if not feature_type in request.response or not feature_id in request.response[feature_type]:
            value = feature_settings['default']()
        else:
            value = request.response[feature_type][feature_id]
        print feature_id,value,type(value)
        return json.dumps({'status':200,'html':render_template(template,**{'admin':False,'id' : feature_id,'value' : value})})


if __name__ == '__main__':
    app.run(debug = True)