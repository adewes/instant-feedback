"""
get_feedback.wsgi
"""
import logging, sys
sys.stdout = sys.stderr
logging.basicConfig(stream=sys.stderr)

root_dir = "/var/www/vhosts/7scientists.com/subdomains/feedback/get_feedback"
activate_this = root_dir+'/venv/bin/activate_this.py'
execfile(activate_this, dict(__file__=activate_this))
import sys
sys.path.insert(0,root_dir)
from get_feedback.app import app
from werkzeug.debug import DebuggedApplication
application = DebuggedApplication(app, True)
