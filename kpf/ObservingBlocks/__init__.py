class OBProperty(object):
    def __init__(self, name='', defaultvalue=None, valuetype=None,
                 comment='', precision=None):
        self.name = name
        self.valuetype = eval(valuetype)
        self._value = None if defaultvalue is None else self.valuetype(defaultvalue)
        self.comment = comment
        self.precision = precision

    def get(self):
        if self._value is not None:
            return self.valuetype(self._value)
        else:
            return self._value

    def set(self, value):
        if value is None:
            self._value = None
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
        self.name_overrides={'2MASSID': 'twoMASSID'}
        self.properties = properties
        for p in properties:
            setattr(self, p['name'], OBProperty(**p))

    def prune(self):
        pass

    def get(self, name):
        name = self.name_overrides.get(name, name)
        this_property = getattr(self, name)
        return this_property.value

    def set(self, name, value):
        name = self.name_overrides.get(name, name)
        if name in [p['name'] for p in self.properties]:
            this_property = getattr(self, name)
            this_property.set(value)

    def from_dict(self, input_dict):
        for key in input_dict.keys():
            input_value = input_dict[key]
            key = self.name_overrides.get(key, key)
            this_property = getattr(self, key)
            this_property.set(input_value)
        self.prune()
        return self

    def to_dict(self):
        self.prune()
        output = {}
        for p in self.properties:
            if self.get(p['name']) is not None:
                output[p['name']] = self.get(p['name'])
        return output

    def to_lines(self, comments=False):
        self.prune()
        lines = []
        for p in self.properties:
            if self.get(p['name']) is not None:
                lines.append(f"{p['name']}: {self.get(p['name'])}")
        return lines

    def validate(self):
        self.prune()
        return True

    def __str__(self):
        output = ''
        for line in self.to_lines():
            output += line+'\n'
        return output

    def __repr__(self):
        output = ''
        for line in self.to_lines():
            output += line+'\n'
        return output
