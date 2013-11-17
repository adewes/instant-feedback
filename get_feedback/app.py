from flask import Flask,render_template,request,make_response,redirect,url_for,abort

import settings
import uuid
import json
import time
import urlparse
import datetime
import re
from collections import defaultdict
from models import Survey,User,Response
from utils import *

from settings import logger

app = Flask(__name__)
app.url_map.converters['regex'] = RegexConverter

@app.route('/')
@with_session()
@with_user()
def welcome():
    context = {'session' : request.session}
    response = make_response(render_template("welcome.html",**context))
    return response

@app.route('/example')
@with_session()
@with_user()
def example():
    survey = Survey.collection.find_one({'user':request.user,'name':'example'})
    if not survey:
        survey = Survey(fields = {},authorized_keys = [],authorized_keys_only = False,key = uuid.uuid4().hex,name = "example",user = request.user)
        survey.save()
    context = {'survey' : survey}
    response = make_response(render_template("example.html",**context))
    return response

@app.route('/login_as/<session_key>')
@with_session()
@with_user()
def login_as(session_key):
    if request.session != session_key:
        request.session = session_key
        return redirect(url_for('index'))
    else:
        context = {'server_url':settings.server_url, 'session_key' : session_key}
        response = make_response(render_template("survey/login_as.html",**context))
        return response

@app.route('/logout')
@with_session()
@with_user()
def logout():
    context = {'server_url':settings.server_url, 'session_key' : request.session}
    request.session = ''
    response = make_response(render_template("survey/logout.html",**context))
    return response
    
@app.route('/survey_menu/<survey_key>')
@with_session()
@with_user()
@with_survey()
@with_admin()
def survey_menu(survey_key):
    context = {'server_url':settings.server_url,'survey':request.survey}
    response = make_response(render_template("survey/menu.html",**context))
    return response

@app.route('/new_field/<survey_key>',methods = ['GET','POST'])
@with_session()
@with_user()
@with_survey()
@with_admin()
def new_field(survey_key):
    if request.method == 'POST':
        path = json.loads(request.form['path'])
        if not 'type' in request.form or not request.form['type'] in settings.field_types:
            abort(404)
        field_id = uuid.uuid4().hex
        field_type = request.form['type']
        field = request.survey.init_field(field_type,field_id)
        field.update_attributes({'path':path})
        request.survey.set_field(field_type,field_id,field)
        request.survey.save()
        return redirect(url_for("edit_field",survey_key = request.survey['key'],field_type = field_type,field_id = field_id))
    context = {'server_url':settings.server_url,'survey':request.survey}
    response = make_response(render_template("survey/new_field.html",**context))
    return response

@app.route('/initialize_survey/<survey_key>',methods = ['GET','POST'])
@with_session()
@with_user()
@with_survey()
@with_response()
@crossdomain(origin='*')
def initialize_survey(survey_key):
    if 'show_summary' in request.args and request.args['show_summary']:
        if not request.user.is_admin(request.survey):
            abort(403)
        view_function = _view_summary_inline
    else:
        view_function = _view_field_inline

    if not 'fields' in request.survey:
        abort(404)
    try:
        discovered_fields = json.loads(request.form['fields'])
    except:
        abort(404)

    fields = request.survey['fields']

    if request.user.is_admin(request.survey):
        for field_type,field_id in discovered_fields:
            if not field_type in fields or not field_id in fields[field_type]:
                field = request.survey.init_field(field_type,field_id)
                request.survey.save()

    fields_with_html = request.survey['fields'].copy()

    for field_type in fields_with_html:
        for field_id in fields_with_html[field_type]:
            field = fields_with_html[field_type][field_id]
            if 'active' in field and field['active'] == False and not request.user.is_admin(request.survey):
                continue
            content = view_function(request.survey['key'],field_type,field_id,return_data = True)
            if content['status'] == 200:
                field['html'] = content['html']
                field['value'] = content['value']
            else:
                del fields_with_html[field_type][field_id]

    survey_parameters = {
                        'response_key' : request.response['response_key'],
                        'fields' : fields_with_html,
                        'admin' : True if request.user.is_admin(request.survey) else False,
                        }

    response = make_response(json.dumps({'status':200, 'survey_parameters':survey_parameters}))
    response.mimetype='text/json'
    return response

def _index():
    surveys = Survey.collection.find({'user':request.user}).sort('_created_at',-1)
    context = {'surveys':surveys}
    response = make_response(render_template("survey/index.html",**context))
    return response

@app.route('/index')
@with_session()
@with_user()    
def index():
    return _index()

@app.route('/details/<survey_key>')
@with_session()
@with_survey()
@with_user()
@with_admin()
def details(survey_key):
    responses = Response.collection.find({'survey_key': request.survey['key']}).count()
    context = {'server_url':settings.server_url, 'survey':request.survey,'responses':responses}
    response = make_response(render_template("survey/details.html",**context))

    return response

@app.route('/summary/<survey_key>')
@with_session()
@with_survey()
@with_user()
@with_admin()
def summary(survey_key):
    responses = Response.collection.find({'survey_key': request.survey['key']}).count()
    context = {'survey':request.survey,'responses':responses}
    response = make_response(render_template("survey/summary.html",**context))

    return response

@app.route('/fields/<survey_key>')
@with_session()
@with_survey()
@with_user()
@with_admin()
def fields(survey_key):
    context = {'survey':request.survey}
    response = make_response(render_template("survey/fields.html",**context))
    return response

@app.route('/export_responses/<survey_key>')
@with_session()
@with_survey()
@with_user()
@with_admin()
def export_responses(survey_key):
    responses = Response.collection.find({'survey_key': request.survey['key']})

    exported_responses = []

    for response in responses:
        exported_fields = {'created_at' : response['_created_at'].strftime("%s"),'updated_at': response['_updated_at'].strftime("%s"),'response_key':response['response_key']}
        for field_type in settings.field_types:
            if field_type in response:
                exported_fields[field_type] = response[field_type]
        exported_responses.append(exported_fields)
    opts = {}
    opts['indent'] = 4
    response = make_response(json.dumps({'fields':request.survey['fields'],'responses':exported_responses},**opts))
    response.mimetype='text/json'
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

@app.route('/delete/<survey_key>',methods = ['GET'])
@with_session()
@with_user()
@with_survey()
@with_admin()
def delete(survey_key):
    context = {'survey':request.survey}
    if 'confirm' in request.args:
        Response.collection.remove({'survey_key':request.survey['key']})
        request.survey.delete()
        return redirect(url_for("index"))
    response = make_response(render_template("survey/delete.html",**context))
    return response

@app.route('/clear_responses/<survey_key>',methods = ['GET'])
@with_session()
@with_user()
@with_survey()
@with_admin()
def clear_responses(survey_key):
    context = {'survey':request.survey}
    if 'confirm' in request.args:
        Response.collection.remove({'survey_key':request.survey['key']})
        return redirect(url_for("details",survey_key = request.survey['key']))
    response = make_response(render_template("survey/clear_responses.html",**context))
    return response

@app.route('/new',methods = ['GET','POST'])
@with_session()
@with_user()
def new():

    error = None
    name = ''
    key = ''

    def form():
        context = {'error':error,'name':name,'key':key}
        response = make_response(render_template("survey/new.html",**context))
        return response

    if request.method == 'POST':
        if not 'name' in request.form or not request.form['name'].strip():
            error = 'You need to supply a name for your survey...'
            return form()
        name = request.form['name']
        if Survey.collection.find({'user':request.user,'name':name}).count():
            error = 'You already have a survey with that name...'
            return form()
        if 'key' in request.form and request.form['key'].strip():
            key = request.form['key']
            if re.search(r"[^\w\d\-]+",key):
                error = "Error: Please use only letters and hyphens for the survey key."
                return form()
        else:
            key = uuid.uuid4().hex
        if Survey.collection.find({'key':key}).count():
            error = 'A survey with this key already exists...'
            return form()
        survey = Survey(fields = {},authorized_keys = [],authorized_keys_only = False,key = key,name = name,user = request.user)
        survey.save()
        return redirect(url_for("details",survey_key = survey['key']))
    else:
        return form()

@app.route('/set_survey_url/<survey_key>',methods = ['POST'])
@with_session()
@with_user()
@with_survey()
@with_admin()
def set_survey_url(survey_key):

    if not "survey_url" in request.form:
        abort(404)

    survey_url = request.form["survey_url"]
    request.survey['survey_url'] = survey_url
    request.survey.save()
    if request_wants_json():
        return json.dumps({'status':200})
    else:
        return redirect(url_for("details",survey_key = request.survey['key']))


@app.route('/authorize_key/<survey_key>',methods = ['GET'])
@with_session()
@with_user()
@with_survey()
@with_admin()
def authorize_key(survey_key):

    if not "response_key" in request.args:
        return json.dumps({'status':404,'message' : 'session_key parameter is missing!'})

    response_key = request.args["response_key"]
    
    if not 'authorized_keys' in request.survey:
        request.survey['authorized_keys'] = []
    if not response_key in request.survey['authorized_keys']:
        request.survey['authorized_keys'].append(response_key)

    request.survey.save()
    if request_wants_json():
        return json.dumps({'status':200})
    else:
        return redirect(url_for("details",survey_key = request.survey['key']))

@app.route('/remove_authorized_key/<survey_key>',methods = ['GET'])
@with_session()
@with_user()
@with_survey()
@with_admin()
def remove_authorized_key(survey_key):

    if not "response_key" in request.args:
        return json.dumps({'status':404,'message' : 'response_key parameter is missing!'})

    response_key = request.args["response_key"]

    if not 'authorized_keys' in request.survey or not response_key in request.survey['authorized_keys']:
        return json.dumps({'status':404,'message' : 'session_key %s not in list of authorized_keys!' % response_key})

    request.survey['authorized_keys'].remove(response_key)
    request.survey.save()

    if request_wants_json():
        return json.dumps({'status':200})
    else:
        return redirect(url_for("details",survey_key = request.survey['key']))

@app.route('/update_response/<survey_key>/<field_type>/<field_id>',methods = ['GET','POST'])
@with_session()
@with_survey()
@with_user()
@with_response()
@with_field()
@jsonp()
@crossdomain(origin='*')
def update_response(survey_key,field_type,field_id):

    if request.survey['authorized_keys_only'] and not request.response['response_key'] in request.survey['authorized_keys'] and not request.user.is_admin(request.survey):
        return json.dumps({'status':403,'html': ''})

    if request.method == 'POST':
        if not "value" in request.form:
            abort(500)
        value = request.form["value"]
    elif request.method == 'GET':
        if not "value" in request.args:
            abort(500)
        value = request.args["value"]

    if not field_type in request.response:
        request.response[field_type] = {}

    parsed_value = request.field.parse_input(value)
    if parsed_value == None and field_id in request.response[field_type]:
        del request.response[field_type][field_id]
    else:
        request.response[field_type][field_id] = parsed_value
    
    request.response.save()

    return _view_field_inline(survey_key,field_type,field_id)

@app.route('/delete_field/<survey_key>/<field_type>/<field_id>',methods = ['GET'])
@with_session()
@with_user()
@with_survey()
@with_admin()
@with_field()
def delete_field(survey_key,field_type,field_id):
    context = {'survey':request.survey,'field_id':field_id,'field_type':field_type}

    if 'confirm' in request.args:
        del request.survey['fields'][field_type][field_id]
        request.survey.save()
        return redirect(url_for('summary',survey_key = survey_key))

    response = make_response(render_template("survey/delete_field.html",**context))
    return response


def _set_field_status(survey_key,field_type,field_id,active = False):
    request.survey['fields'][field_type][field_id]['active'] = active
    request.survey.save()
    context = {'survey_key' : survey_key,'field':request.field.attributes,'field_type':field_type,'field_id':field_id,'context':request.field.edit_context(),'success':True}
    response = make_response(render_template("/survey/fields/"+field_type+"/edit.html",**context))
    return response

@app.route('/activate_field/<survey_key>/<field_type>/<field_id>',methods = ['GET'])
@with_session()
@with_user()
@with_survey()
@with_admin()
@with_field()
def activate_field(survey_key,field_type,field_id):
    return _set_field_status(survey_key,field_type,field_id,active = True)
    
@app.route('/deactivate_field/<survey_key>/<field_type>/<field_id>',methods = ['GET'])
@with_session()
@with_user()
@with_survey()
@with_admin()
@with_field()
def deactivate_field(survey_key,field_type,field_id):
    return _set_field_status(survey_key,field_type,field_id,active = False)
    
@app.route('/edit_field/<survey_key>/<field_type>/<field_id>',methods = ['GET','POST'])
@with_session()
@with_user()
@with_survey()
@with_admin()
@with_field()
@crossdomain(origin='*')
def edit_field(survey_key,field_type,field_id):

    if not field_type in settings.field_types:
        abort(500)
    error = None
    context = {'survey_key' : survey_key,'field':request.field.attributes,'field_type':field_type,'field_id':field_id,'context':request.field.edit_context()}
    if request.method == 'POST':
        try:
            request.field.update_attributes(request.form)
            request.survey.set_field(field_type,field_id,request.field)
            request.survey.save()
        except ValueError as e:
            error = str(e)
        if not error:
            context['success'] = True
        else:
            context['error'] = error
    else:
        pass
    response = make_response(render_template("/survey/fields/"+field_type+"/edit.html",**context))
    return response


def _view_field_inline(survey_key,field_type,field_id,return_data = False):

    if request.survey['authorized_keys_only'] and not request.response['response_key'] in request.survey['authorized_keys'] and not request.user.is_admin(request.survey):
        return json.dumps({'status':403,'html': ''})
    try:
        request.field = request.survey.get_field(field_type,field_id)
    except AttributeError:
        if request.user.is_admin(request.survey):
            request.field = request.survey.init_field(field_type,field_id)
            request.survey.save()
        else:
            abort(403)

    if not field_type in request.response or not field_id in request.response[field_type]:
        value = request.field.default_value()
    else:
        value = request.response[field_type][field_id]
    value = request.field.value_context(value)

    data = {'status':200,'value':value,'html':render_template('/survey/fields/'+field_type+'/_field_inline.html',**{'field':request.field.attributes,'is_admin':request.user.is_admin(request.survey),'field_type':field_type,'field_id' : field_id,'value' : value,'survey_key':survey_key,'server_url':settings.server_url })}

    if return_data:
        return data

    return json.dumps(data)

def _view_summary_inline(survey_key,field_type,field_id,return_data = False):

    try:
        field = request.survey.get_field(field_type,field_id)
    except AttributeError:
        abort(403)

    responses = list(Response.collection.find({'survey_key' : survey_key}))

    try:
        summary = field.aggregate(responses)[field_id]
    except KeyError:
        summary = {}

    data = {'status':200,'value':summary,'html':render_template('/survey/fields/'+field_type+'/_summary_inline.html',**{'summary':summary,'field_type':field_type, 'field_id' : field_id,'field':field.attributes,'survey_key':survey_key,'server_url':settings.server_url,'is_admin':request.user.is_admin(request.survey)})}

    if return_data:
        return data

    return json.dumps(data)

@app.route('/view_summary_inline/<survey_key>/<field_type>/<field_id>',methods = ['GET'])
@with_session()
@with_user()
@with_survey()
@with_admin()
@with_response()
@jsonp()
@crossdomain(origin='*')
def view_summary_inline(survey_key,field_type,field_id):

    if not field_type in settings.field_types:
        abort(500)

    return _view_summary_inline(survey_key,field_type,field_id)

@app.route('/view_summary/<survey_key>/<field_type>/<field_id>',methods = ['GET'])
@with_session()
@with_user()
@with_survey()
@with_admin()
@with_response()
@with_field()
@crossdomain(origin='*')
def view_summary(survey_key,field_type,field_id):

    if not field_type in settings.field_types:
        abort(500)

    responses = list(Response.collection.find({'survey_key' : survey_key}))
    try:
        summary = request.field.aggregate(responses)[field_id]
    except KeyError:
        summary = {}

    context = {'survey_key' : survey_key,'field':request.field.attributes,'field_type':field_type,'field_id':field_id,'summary':summary}
    response = make_response(render_template("/survey/fields/"+field_type+"/summary.html",**context))
    return response

@app.route('/view_field_inline/<survey_key>/<field_type>/<field_id>',methods = ['GET'])
@with_session()
@with_survey()
@with_user()
@with_response()
@jsonp()
@crossdomain(origin='*')
def view_field_inline(survey_key,field_type,field_id):
    return _view_field_inline(survey_key,field_type,field_id)

@app.route('/feedback.js',methods = ['GET'])
@with_session()
def feedback_js():
    return _feedback_js(with_jquery = False)

@app.route('/feedback_with_jquery.js',methods = ['GET'])
@with_session()
def feedback_with_jquery_js():
    return _feedback_js(with_jquery = True)

def _feedback_js(with_jquery = False):
    file_content = "\n".join([f.read() for f in [open(settings.project_path+filename,"r") for filename in (settings.jquery_files if with_jquery else [])+settings.javascript_files ]])
    response = make_response(file_content)
    response.mimetype='application/javascript'
    return response

@app.route('/feedback.css',methods = ['GET'])
@with_session()
def feedback_css():
    file_content = "\n".join([f.read() for f in [open(settings.project_path+filename,"r") for filename in settings.css_files]])
    response = make_response(file_content)
    response.mimetype='text/css'
    return response

if __name__ == '__main__':
    app.run(debug = True,host = '0.0.0.0')
