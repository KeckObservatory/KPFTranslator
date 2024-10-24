class OBProperty(object):
    def __init__(self, name, value, valuetype, comment=''):
        self.name = name
        self.value = value if value is None else valuetype(value)
        #self.value = valuetype(value)
        self.valuetype = valuetype
        self.comment = comment

    def get(self):
        return self.valuetype(self.value)

    def get_type(self):
        return self.valuetype

    def get_comment(self):
        return self.comment

    def set(self, value):
        try:
            self.value = self.valuetype(value)
        except TypeError:
            raise TypeError(f"Input {value} can not be cast as {self.valuetype}")


class BaseOBComponent(object):
    def __init__(self, component_type, version, properties=[]):
        self.type = component_type
        self.version = version
        self.name_overrides={'2MASSID': 'twoMASSID'}
        self.properties = properties
        for p in properties:
            setattr(self, p[0], OBProperty(*p))

    def get(self, name):
        name = self.name_overrides.get(name, name)
        this_property = getattr(self, name)
        return this_property.value

    def set(self, name, value):
        name = self.name_overrides.get(name, name)
        if name in [p[0] for p in self.properties]:
            this_property = getattr(self, name)
            this_property.set(value)

    def from_dict(self, input_dict):
        for key in input_dict.keys():
            self.set(key, input_dict[key])
        return self

    def to_dict(self):
        output = {}
        for p in self.properties:
            if self.get(p[0]) is not None:
                output[p[0]] = self.get(p[0])
        return output

    def to_lines(self, comments=False):
        lines = []
        for p in self.properties:
            if self.get(p[0]) is not None:
                lines.append(f"{p[0]}: {self.get(p[0])}")
        return lines

    def validate(self):
        return True

    def __str__(self):
        output = ''
        for line in self.to_lines():
            output += line+'\n'
        return output

    def __repr__(self):
        return self.__str__()
