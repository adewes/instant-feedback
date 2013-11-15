import pymongo
from collections import defaultdict
from flask import abort
import fields
import logging
import sys
import os.path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

ch = logging.StreamHandler(sys.stdout)
ch.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
ch.setFormatter(formatter)
logger.addHandler(ch)

protocol = 'http://'

db = pymongo.MongoClient().survey

project_path = os.path.abspath(__file__+"/../../")

field_types = {
    'check': fields.Check,
    'rate': fields.Rate,
    'vote': fields.Vote,
    'input': fields.Input,
    'select':fields.Select,
}

javascript_files = ["/static/feedback.js"]
css_files = ["/static/feedback.css"]