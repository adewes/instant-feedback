import pymongo
from collections import defaultdict
from flask import abort
import fields
import logging
import sys

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

ch = logging.StreamHandler(sys.stdout)
ch.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
ch.setFormatter(formatter)
logger.addHandler(ch)

server_name = 'feedback.7scientists.com'

db = pymongo.MongoClient().survey

field_types = {
    'check': fields.Check,
#    'scale': fields.Scale,
    'rate': fields.Rate,
    'vote': fields.Vote,
    'input': fields.Input,
    'select':fields.Select,
}