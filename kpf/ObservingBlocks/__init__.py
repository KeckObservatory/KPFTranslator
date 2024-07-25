class OBProperty(object):
    def __init__(self, name, value, valuetype):
        self.name = name
        self.value = valuetype(value)
        self.valuetype = valuetype

    def get(self):
        return self.value

    def set(self, value):
        self.value = value


class BaseOBComponent(object):
    def __init__(self):
        self.OBtype = None
        self.OBversion = 2.0
        self.name_overrides = {'2MASSID': 'twoMASSID'}

    def get(self, name):
        name = self.name_overrides.get(name, name)
        thisOBproperty = getattr(self, name)
        return thisOBproperty.value

    def set(self, name, value):
        name = self.name_overrides.get(name, name)
        try:
            thisOBproperty = getattr(self, name)
            thisOBproperty.set(value)
        except AttributeError as e:
            print(f"AttributeError setting {name}. skipping")

    def to_lines():
        pass

    def __str__(self):
        output = ''
        for line in self.lines:
            output += line+'\n'
        return output

    def __repr__(self):
        self.__str__()
