from flask import Flask,render_template,request,make_response,redirect,url_for,abort

import settings
import uuid
import json
import time
import urlparse
from collections import defaultdict
from models import Survey,User,Response
from utils import *

from settings import logger

app = Flask(__name__)

@app.route('/')
@with_session()
@with_user()
def welcome():
    context = {'session' : request.session}
    response = make_response(render_template("welcome.html",**context))
    return response

@app.route('/index')
@with_session()
@with_user()    
def index():
    surveys = Survey.collection.find({'user':request.user})
    context = {'surveys':surveys}
    response = make_response(render_template("survey/index.html",**context))
    return response

@app.route('/details/<survey_key>')
@with_session()
@with_survey()
@with_user()
@with_admin()
def details(survey_key):
    responses = Response.collection.find({'survey_key': request.survey['key']}).count()
    context = {'survey':request.survey,'responses':responses}
    response = make_response(render_template("survey/details.html",**context))

    return response

@app.route('/toogle_authorized_keys_only/<survey_key>')
@with_session()
@with_user()
@with_survey()
@with_admin()
def toggle_authorized_keys_only(survey_key):

    if not 'authorized_keys_only' in request.survey:
        request.survey['authorized_keys_only'] = True

    request.survey['authorized_keys_only'] = not request.survey['authorized_keys_only']
    request.survey.save()
    return redirect(url_for("details",survey_key = request.survey['key']))

@app.route('/clear_authorized_keys/<survey_key>')
@with_session()
@with_user()
@with_survey()
@with_admin()
def clear_authorized_keys(survey_key):
    request.survey['authorized_keys'] = []
    request.survey.save()
    return redirect(url_for("details",survey_key = request.survey['key']))

@app.route('/new',methods = ['GET','POST'])
@with_session()
@with_user()
def new():

    context = {}

    if request.method == 'POST':
        survey = Survey(fields = {},authorized_keys = [],authorized_keys_only = False,key = uuid.uuid4().hex,name = request.form['name'],user = request.user)
        survey.save()
        return redirect(url_for("details",survey_key = survey['key']))
    else:
        response = make_response(render_template("survey/new.html",**context))

    return response

def request_wants_json():
    best = request.accept_mimetypes \
        .best_match(['application/json', 'text/html'])
    return best == 'application/json' and \
        request.accept_mimetypes[best] > \
        request.accept_mimetypes['text/html']

@app.route('/authorize_session_key/<survey_key>',methods = ['GET'])
@with_session()
@with_user()
@with_survey()
@with_admin()
def authorize_session_key(survey_key):

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
        return redirect(url_for("details",survey_key = request.survey['key']))

@app.route('/remove_session_key/<survey_key>',methods = ['GET'])
@with_session()
@with_user()
@with_survey()
@with_admin()
def remove_session_key(survey_key):

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
        return redirect(url_for("details",survey_key = request.survey['key']))

@app.route('/update_response/<survey_key>/<field_type>/<field_id>',methods = ['GET','POST'])
@with_session()
@with_user()
@with_survey()
@with_response()
@with_field()
def update_response(survey_key,field_type,field_id):

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

    template = request.field.template
    parsed_value = request.field.parse_input(value)

    if not field_type in request.response:
        request.response[field_type] = {}

    request.response[field_type][field_id] = parsed_value
    request.response.save()

    return _get_html(survey_key,field_type,field_id)

@app.route('/update_field/<survey_key>/<field_type>/<field_id>',methods = ['POST'])
@with_session()
@with_user()
@with_survey()
@with_response()
@with_admin()
@with_field()
def update_field(survey_key,field_type,field_id):

    if not field_type in settings.field_types:
        abort(500)

    request.field.update_attributes(dict([(x[0],x[1] if len(x[1]) > 1 else x[1][0]) for x in urlparse.parse_qsl(request.form['attributes'])]))

    request.survey.set_field(field_type,field_id,request.field)
    request.survey.save()

    return _get_html(survey_key,field_type,field_id)

@app.route('/get_html/<survey_key>/<field_type>/<field_id>',methods = ['GET'])
@with_session()
@with_user()
@with_survey()
@with_response()
def get_html(survey_key,field_type,field_id):
    return _get_html(survey_key,field_type,field_id)

def _get_html(survey_key,field_type,field_id):


    if request.survey['authorized_keys_only'] and not request.response['session'] in request.survey['authorized_keys']:
        return json.dumps({'status':403,'html': ''})

    try:
        request.field = request.survey.get_field(field_type,field_id)
    except AttributeError:
        if request.user.is_admin(request.survey):
            request.field = request.survey.init_field(field_type,field_id)
            request.survey.save()
        else:
            abort(403)

    template = request.field.template

    if not field_type in request.response or not field_id in request.response[field_type]:
        value = request.field.default_value()
    else:
        value = request.response[field_type][field_id]
    value = request.field.provide_context(value)
    return json.dumps({'status':200,'value':value,'html':render_template(template,**{'field':request.field.attributes,'show_summary': False, 'is_admin':request.user.is_admin(request.survey),'field_type':field_type,'field_id' : field_id,'value' : value })})

def generate_summary(survey,field_type,field_id):

    responses = list(Response.collection.find({'survey_key' : survey['key']}))

    if not len(responses):
        abort(404)

    summary = request.field.aggregate(responses)

    if not field_id in summary:
        abort(404)

    return summary[field_id]


@app.route('/show_summary/<survey_key>/<field_type>/<field_id>',methods = ['GET'])
@with_session()
@with_user()
@with_survey()
@with_admin()
@with_response()
@with_field()
def show_summary(survey_key,field_type,field_id):

    if not field_type in settings.field_types:
        abort(500)

    template =settings.field_types[field_type].template

    summary = generate_summary(request.survey,field_type,field_id)

    return json.dumps({'status':200,'admin':True,'value':summary,'html':render_template(template,**{'summary':summary,'show_summary':True,'field_type':field_type,'field_id' : field_id,'field':request.field.attributes})})

if __name__ == '__main__':
    app.run(debug = True,host = '0.0.0.0')
