import pymongo
from collections import defaultdict
from flask import abort

db = pymongo.MongoClient().survey

#Choose a secret string that allows admin access...
ADMIN_SECRET = 'notasecret'

def vote_aggregator(responses):
    counts = defaultdict(lambda : {'up':0,'down':0})
    for response in responses:
        for vote_id in response['vote']:
            if response['vote'][vote_id] == 1:
                counts[vote_id]['up']+=1
            elif response['vote'][vote_id] == -1:
                counts[vote_id]['down']+=1
    return counts

def input_aggregator(responses):
    frequencies = defaultdict(lambda : defaultdict(lambda :0) )
    for response in responses:
        for input_id in response['input']:
            frequencies[input_id][response['input'][input_id]]+=1
    for input_id in frequencies:
        frequencies[input_id] = sorted(frequencies[input_id].items(),key = lambda x:-x[1])
    print frequencies
    return frequencies

def rate_aggregator(responses):
    counts = defaultdict(lambda: {'n':0,'average':0,'distribution':defaultdict(lambda :0)})
    for response in responses:
        for rate_id in response['rate']:
            d = counts[rate_id]
            value = response['rate'][rate_id]
            d['average']=(d['average']*d['n']+value)/(float(d['n'])+1)
            d['n']+=1
            d['distribution'][value]+=1
    return counts

def vote_parser(input):
    try:
        x = int(input)
    except ValueError:
        abort(500)
    if x not in (1,-1,0):
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

feature_types = {
    'rate': {'template' : '_rate.html','aggregator' : rate_aggregator,'parser': rate_parser,'default': lambda :0},
    'vote': {'template' : '_vote.html','aggregator' : vote_aggregator,'parser': vote_parser,'default': lambda :0},
    'input': {'template' : '_input.html','aggregator' : input_aggregator,'parser':lambda x:x,'default': lambda :''},
}