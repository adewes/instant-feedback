from flask import abort
from collections import defaultdict

class BaseField(object):

    def __init__(self,attributes):
        self.attributes = attributes

    def update_attributes(self,attributes):
        self.attributes = attributes
        return self.attributes

    def value_context(self,value):
        return value

    def edit_context(self):
        return {}

class Select(BaseField):

    def default_value(self):
        return ''

    def aggregate(self,responses,args = None):
        if not 'choices' in self.attributes:
            return {}
        frequencies = defaultdict(lambda : {'n':0,'distribution':defaultdict(lambda :0)} )
        for response in responses:
            if not 'select' in response:
                continue
            for select_id in response['select']:
                frequencies[select_id]['distribution'][response['select'][select_id]]+=1
                frequencies[select_id]['n']+=1
        for select_id in frequencies:
            frequencies[select_id]['distribution'] = [(self.attributes['choices'][x[0]][1],x[1]) for x in sorted(frequencies[select_id]['distribution'].items(),key = lambda x:-x[1]) if x[0] < len(self.attributes['choices'])]
        return frequencies

    def parse_input(self,input):
        if not input.strip():
            return None
        return int(input)

    def value_context(self,value):
        d = {'i':value}
        if not 'choices' in self.attributes:
            return d
        if value < len(self.attributes['choices']):
            d['choice'] = self.attributes['choices'][value][1]
        return d

    def update_attributes(self,attributes):
        if not 'choices' in attributes:
            raise AttributeError()
        self.attributes['choices_str'] = attributes['choices']
        self.attributes['choices'] = list(enumerate([s.strip() for s in attributes['choices'].split("\n")]))
        return self.attributes


class Check(BaseField):

    def default_value(self):
        return 0

    def aggregate(self,responses,args = None):
        counts = defaultdict(lambda : 0)
        for response in responses:
            if not 'check' in response:
                continue
            for check_id in response['check']:
                if response['check'][check_id] == 1:
                    counts[check_id]+=1
        return counts

    def parse_input(self,input):
        try:
            input = int(input)
        except ValueError:
            abort(500)
        if input not in (1,0):
            abort(500)
        return input


class Rate(BaseField):

    def default_value(self):
        return 0

    def update_attributes(self,attributes):
        sanitized_attributes = {}
        for key,value in attributes.items():
            sanitized_attributes[key] = value
        if 'n' in sanitized_attributes:
            if not sanitized_attributes['n']:
                del sanitized_attributes['n']
            else:
                try:
                    sanitized_attributes['n'] = int(attributes['n'])
                except ValueError:
                    raise ValueError("Invalid value for n:%s" % sanitized_attributes['n'])
                if sanitized_attributes['n'] > 10:
                    raise ValueError("Maximum allowed value for n: 10")
        super(Rate,self).update_attributes(sanitized_attributes)

    def aggregate(self,responses,args = None):
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

    def parse_input(self,input):
        try:
            input = int(input)
        except ValueError:
            abort(500)
        max_value = self.attributes['n'] if 'n' in self.attributes else 5
        if input <= 0 or input > max_value:
            abort(500)
        return input

class Input(BaseField):

    def default_value(self):
        return ''

    def aggregate(self,responses,args = None):
        frequencies = defaultdict(lambda : {'truncated':False,'frequencies' :defaultdict(lambda :0),'responses':0} )
        for response in responses:
            if not 'input' in response:
                continue
            for input_id in response['input']:
                frequencies[input_id]['frequencies'][response['input'][input_id]]+=1
                frequencies[input_id]['responses']+=1
        for input_id in frequencies:
            frequencies[input_id]['frequencies'] = sorted(frequencies[input_id]['frequencies'].items(),key = lambda x:-x[1])
            if len(frequencies[input_id]['frequencies']) > 100:
                frequencies[input_id]['truncated'] = True
                frequencies[input_id]['frequencies'] = frequencies[input_id]['frequencies'][:100]
        return frequencies

    def parse_input(self,input):
        return input


class Scale(BaseField):

    def default_value(self):
        return 0

    def aggregate(self,responses,args = None):
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

    def parse_input(self,input):
        try:
            input = float(input)
        except ValueError:
            abort(500)
        if input < -1.0  or input > 1.0:
            abort(500)
        return input

class Vote(BaseField):

    def default_value(self):
        return 0


    def aggregate(self,responses,args = None):
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

    def parse_input(self,input):
        try:
            input = int(input)
        except ValueError:
            abort(500)
        if input not in (1,-1,0):
            abort(500)
        return input
