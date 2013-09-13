import pymongo
from collections import defaultdict
from flask import abort

db = pymongo.MongoClient().survey

#Choose a secret string that allows admin access...
ADMIN_SECRET = 'notasecret'

def vote_aggregator(responses):
    counts = defaultdict(lambda : {'up':0,'down':0})
    for response in responses:
        if not 'vote' in response:
            continue
        for vote_id in response['vote']:
            if response['vote'][vote_id] == 1:
                counts[vote_id]['up']+=1
            elif response['vote'][vote_id] == -1:
                counts[vote_id]['down']+=1
    return counts

def check_aggregator(responses):
    counts = defaultdict(lambda : 0)
    for response in responses:
        if not 'check' in response:
            continue
        for check_id in response['check']:
            if response['check'][check_id] == 1:
                counts[check_id]+=1
    return counts

def input_aggregator(responses):
    frequencies = defaultdict(lambda : defaultdict(lambda :0) )
    for response in responses:
        if not 'input' in response:
            continue
        for input_id in response['input']:
            frequencies[input_id][response['input'][input_id]]+=1
    for input_id in frequencies:
        frequencies[input_id] = sorted(frequencies[input_id].items(),key = lambda x:-x[1])
    print frequencies
    return frequencies

def rate_aggregator(responses):
    counts = defaultdict(lambda: {'n':0,'average':0,'distribution':defaultdict(lambda :0)})
    for response in responses:
        if not 'rate' in response:
            continue
        for rate_id in response['rate']:
            d = counts[rate_id]
            value = response['rate'][rate_id]
            d['average']=(d['average']*d['n']+value)/(float(d['n'])+1)
            d['n']+=1
            d['distribution'][value]+=1
    return counts

def scale_aggregator(responses):
    counts = defaultdict(lambda: {'n':0,'average':0})
    for response in responses:
        if not 'scale' in response:
            continue
        for scale_id in response['scale']:
            d = counts[scale_id]
            value = response['scale'][scale_id]
            d['average']=(d['average']*d['n']+value)/(float(d['n'])+1)
            d['n']+=1
    return counts

def vote_parser(input):
    try:
        x = int(input)
    except ValueError:
        abort(500)
    if x not in (1,-1,0):
        abort(500)
    return x

def check_parser(input):
    try:
        x = int(input)
    except ValueError:
        abort(500)
    if x not in (1,0):
        abort(500)
    return x

def rate_parser(input):
    try:
        x = int(input)
    except ValueError:
        abort(500)
    if x <= 0 or x > 5:
        abort(500)
    return x

def scale_parser(input):
    try:
        x = float(input)
    except ValueError:
        abort(500)
    if x < -1.0  or x > 1.0:
        abort(500)
    return x

feature_types = {
    'check': {'template' : '_check.html','aggregator' : check_aggregator,'parser': check_parser,'default': lambda :0},
    'scale': {'template' : '_scale.html','aggregator' : scale_aggregator,'parser': scale_parser,'default': lambda :0},
    'rate': {'template' : '_rate.html','aggregator' : rate_aggregator,'parser': rate_parser,'default': lambda :0},
    'vote': {'template' : '_vote.html','aggregator' : vote_aggregator,'parser': vote_parser,'default': lambda :0},
    'input': {'template' : '_input.html','aggregator' : input_aggregator,'parser':lambda x:x,'default': lambda :''},
}