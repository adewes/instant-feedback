from flask import Flask,render_template,request,make_response,redirect,url_for,abort

import settings
import uuid
import json
import time
from collections import defaultdict

app = Flask(__name__)

def _get_session():
    session = request.cookies.get('session')
    if not session:
    	print "Creating session..."
    	session = uuid.uuid4().hex
    return session

def _get_response(survey_key,session):
    response = settings.db.responses.find_one({'survey':survey_key,'session':session})
    if not response:
    	response = {'session':session,'survey':survey_key,'ip':request.remote_addr}

    for feature_type in settings.feature_types:
        if not feature_type in response:
            response[feature_type] = {}

    return response

def _get_summary(survey_key):
    responses = list(settings.db.responses.find({'survey':survey_key}))
    summary = {}
    for key in settings.feature_types:
        aggregator = settings.feature_types[key]['aggregator']
        summary[key] = aggregator(responses)
    return summary

def _save_response(response):
	settings.db.responses.save(response)

def _update_response(survey_key,feature_id,value,feature_type = 'votes'):
    session = _get_session()
    response = _get_response(survey_key,session)
    if not feature_type in response:
        response[feature_type] = {}
    response[feature_type][feature_id] = value
    _save_response(response)
    return response

@app.route('/')
def survey():

    if 'admin' in request.args:
        admin = request.args['admin']
    else:
        admin = ''

    session = _get_session()
    context = {'session' : session,'admin':admin}

    response = make_response(render_template("survey.html",**context))
    response.set_cookie('session',session)

    return response

def request_wants_json():
    best = request.accept_mimetypes \
        .best_match(['application/json', 'text/html'])
    return best == 'application/json' and \
        request.accept_mimetypes[best] > \
        request.accept_mimetypes['text/html']

@app.route('/update_response/<survey_key>/<feature_type>/<feature_id>',methods = ['GET','POST'])
def update_response(survey_key,feature_type,feature_id):
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
    print feature_type,feature_id,value
    feature_settings = settings.feature_types[feature_type]
    parser = feature_settings['parser']
    template =feature_settings['template']
    parsed_value = parser(value)
    response = _update_response(survey_key,feature_id,parsed_value,feature_type)
    value = response[feature_type][feature_id]
    return json.dumps({'status':200,'html':render_template(template,**{'id' : feature_id,'value' : value})})
    
@app.route('/get_html/<survey_key>/<feature_type>/<feature_id>',methods = ['GET'])
def get_html(survey_key,feature_type,feature_id):
    session = _get_session()

    feature_settings = settings.feature_types[feature_type]
    template =feature_settings['template']

    if 'admin' in request.args and request.args['admin'] == settings.ADMIN_SECRET:
        admin = True
        summary = _get_summary(survey_key)
        if not feature_type in summary or not feature_id in summary[feature_type]:
            abort(404)
        return json.dumps({'status':200,'html':render_template(template,**{'summary':summary[feature_type][feature_id],'admin':True,'id' : feature_id})})
    else:
        summary = {}
        response = _get_response(survey_key,session)
        if not feature_type in response or not feature_id in response[feature_type]:
            value = feature_settings['default']()
            print "default value for %s: %s" % (feature_id,str(value))
        else:
            value = response[feature_type][feature_id]
        return json.dumps({'status':200,'html':render_template(template,**{'admin':False,'id' : feature_id,'value' : value})})


if __name__ == '__main__':
    app.run(debug = True,host = '0.0.0.0')
