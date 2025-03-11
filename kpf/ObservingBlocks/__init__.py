import os
import json
import requests
import urllib3
urllib3.disable_warnings() # We're going to do verify=False, so ignore warnings

from kpf import log, cfg


class OBProperty(object):
    def __init__(self, name='', defaultvalue=None, valuetype=None,
                 comment='', precision=None, altname=None):
        self.name = name if altname is None else altname
        self.valuetype = eval(valuetype)
        self._value = None if defaultvalue is None else self.valuetype(defaultvalue)
        self.comment = comment
        self.precision = precision
        self.defaultvalue = defaultvalue

    def get(self, string=False):
        if self._value is not None and string == False:
            return self.valuetype(self._value)
        elif self._value is not None and string == True:
            return self.__str__()
        else:
            return self._value

    def set(self, value):
        if value is None:
            self._value = self.defaultvalue
        else:
            try:
                self._value = self.valuetype(value)
            except TypeError:
                raise TypeError(f"Input {value} can not be cast as {self.valuetype}")

    def __str__(self):
        if self.valuetype == float and self.precision is not None:
            return ('{0:.%df}' % self.precision).format(self._value)
        return f"{self._value}"

    def __repr__(self):
        return f"{self._value}"

    # creating a property object
    value = property(get, set)


class BaseOBComponent(object):
    def __init__(self, component_type, version, properties=[]):
        self.type = component_type
        self.version = version
        self.properties = properties
        for p in properties:
            all_properties = ['name', 'defaultvalue', 'valuetype',
                              'comment', 'precision', 'altname']
            for pname in all_properties:
                if pname not in p.keys():
                    p[pname] = None
            setattr(self, p['name'], OBProperty(**p))
        self.pruning_guide = []
        self.list_element = False

    def get_property_name(self, name):
        for p in self.properties:
            if name in [p['name'], p['altname']]:
                return p['name']

    def get_text_name(self, name):
        for p in self.properties:
            if name in [p['name'], p['altname']]:
                return p['altname'] if p['altname'] is not None else p['name']

    def get(self, name, string=False):
        name = self.get_property_name(name)
        this_property = getattr(self, name)
        if string == True and this_property.valuetype != str:
            return this_property.__str__()
        elif string == True and this_property.valuetype == str:
            return f"'{this_property.__str__()}'"
        else:
            return this_property.value

    def set(self, name, value):
        name = self.get_property_name(name)
        if name in [p['name'] for p in self.properties]:
            this_property = getattr(self, name)
            this_property.set(value)

    def from_dict(self, input_dict):
        for key in input_dict.keys():
            input_value = input_dict[key]
            key = self.get_property_name(key)
            try:
                this_property = getattr(self, key)
                this_property.set(input_value)
            except AttributeError as e:
                print(f"No property named {key}")
        return self

    def to_dict(self):
        output = {}
        for p in self.properties:
            name = self.get_text_name(name)
            if self.get(p['name']) is not None:
                outname = p['name'] if p['altname'] is None else p['altname']
                output[outname] = self.get(p['name'])
        return output

    def to_lines(self, prune=True, comment=False):
        prune_list = []
        if prune == True:
            for prune in self.pruning_guide:
                if prune[0] == True:
                    prune_list.extend(prune[1])
        lines = []
        for i,p in enumerate(self.properties):
            if self.get(p['name']) is not None and p['name'] not in prune_list:
                outname = p['name'] if p['altname'] is None else p['altname']
                outtext = f"{self.get(p['name'], string=True)}"
                prepend = '- ' if self.list_element == True and i == 0 else '  '
                comment_text = self.add_comment(p['name']) if comment == True else ''
                lines.append(f"{prepend}{outname}: {outtext}{comment_text}")
        return lines

    def add_comment(self, pname):
        return ''

    def validate(self):
        return True

    def __str__(self):
        output = ''
        for line in self.to_lines():
            output += line+'\n'
        return output

    def __repr__(self, prune=True, comment=False):
        '''Show the full text representation of the object as it would appear
        in a YAML input file.
        '''
        output = ''
        for line in self.to_lines(prune=prune, comment=comment):
            output += line+'\n'
        return output


def query_database(query='getKPFObservingBlock', params={}):
    if 'hash' not in params.keys():
        params['hash'] = os.getenv('APIHASH', default='')
    url = cfg.get('Database', 'url')
    log.debug(f"Running database query: {query}")
    log.debug(params)
    r = requests.post(f"{url}{query}", json=params, verify=False)
    try:
        result = json.loads(r.text)
    except Exception as e:
        log.error(f'Failed to parse result:')
        log.error(r.text)
        log.error(e)
        return None

    OBs = []
    log.debug(f'{query} retrieved {len(result)} results')
    for entry in result:
        try:
            OB = ObservingBlock(entry)
            OBs.append(OB)
        except Exception as e:
            log.error('Unable to parse result in to an ObservingBlock')
            log.debug(entry)
            log.error(e)
    log.debug(f'{query} parsed {len(OBs)} ObservingBlocks')
    return OBs