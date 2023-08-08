from pathlib import Path
import yaml


##-------------------------------------------------------------------------
## OB Data Model
##-------------------------------------------------------------------------
class OBProperty(object):
    def __init__(self, name, value, valuetype):
        self.name = name
        self.value = value
        self.valuetype = valuetype

    def get(self):
        return self.value

    def set(self, value):
        self.value = value


class BaseOB(object):
    def __init__(self):
        self.lines = []
        self.OBtype = None
        self.OBversion = None

    def get(self, name):
        thisOBproperty = getattr(self, name)
        return thisOBproperty.value

    def set(self, name, value):
        thisOBproperty = getattr(self, name)
        thisOBproperty.set(value)

#     @classmethod
#     def load_from_file(self, fname):
#         try:
#             with open(fname, 'r') as f:
#                 OBdict = yaml.safe_load(f)
#             if OBdict.get('Template_Name', None) == 'kpf_sci':
#                 OB = ScienceOB(OBdict)
#                 if OBdict.get('star_list_line', None) is not None:
#                     OB.star_list_line = OBdict.get('star_list_line')
#                 else:
#                     OB.star_list_line = ''
#             elif OBdict.get('Template_Name', None) == 'kpf_cal':
#                 OB = CalibrationOB(OBdict)
#         except Exception as e:
#             pass
#         OB.to_lines()
#         return OB

    def to_lines():
        pass

    def write_to_file(self, file):
        file = Path(file)
        if file.exists() is True: file.unlink()
        with open(file, 'w') as f:
            for line in self.lines:
                f.write(line+'\n')

    def __str__(self):
        output = ''
        for line in self.lines:
            output += line+'\n'
        return output

    def __repr__(self):
        output = ''
        for line in self.lines:
            output += line+'\n'
        return output


class SEQ_Observations(BaseOB):
    def __init__(self, input_dict):
        self.OBtype = 'SEQ_Observations'
        self.Object = OBProperty('Object', input_dict.get('Object', ''), str)
        self.nExp = OBProperty('nExp', input_dict.get('nExp', 1), int)
        self.ExpTime = OBProperty('ExpTime', input_dict.get('ExpTime', 1), float)
        self.ExpMeterMode = OBProperty('ExpMeterMode', input_dict.get('ExpMeterMode', 'monitor'), str)
        self.ExpMeterExpTime = OBProperty('ExpMeterExpTime', input_dict.get('ExpMeterExpTime', 1), float)
        self.AutoExpMeter = OBProperty('AutoExpMeter', input_dict.get('AutoExpMeter', False), bool)
        self.TakeSimulCal = OBProperty('TakeSimulCal', input_dict.get('TakeSimulCal', True), bool)
        self.AutoNDFilters = OBProperty('AutoNDFilters', input_dict.get('AutoNDFilters', False), bool)
        self.CalND1 = OBProperty('CalND1', input_dict.get('CalND1', 'OD 0.1'), str)
        self.CalND2 = OBProperty('CalND2', input_dict.get('CalND2', 'OD 0.1'), str)

    def to_lines(self):
        self.lines = []
        self.lines += [f" - Object: {self.get('Object')}"]
        self.lines += [f"   nExp: {self.get('nExp')}"]
        self.lines += [f"   ExpTime: {self.get('ExpTime')}"]
        self.lines += [f"   ExpMeterMode: {self.get('ExpMeterMode')}"]
        self.lines += [f"   AutoExpMeter: {self.get('AutoExpMeter')}"]
        if not self.get('AutoExpMeter'):
            self.lines += [f"   ExpMeterExpTime: {self.get('ExpMeterExpTime')}"]
        self.lines += [f"   TakeSimulCal: {self.get('TakeSimulCal')}"]
        if self.get('TakeSimulCal'):
            self.lines += [f"   AutoNDFilters: {self.get('AutoNDFilters')}"]
            if not self.get('AutoNDFilters'):
                self.lines += [f"   CalND1: {self.get('CalND1')}"]
                self.lines += [f"   CalND2: {self.get('CalND2')}"]
        return self.lines


class SEQ_Darks(BaseOB):
    def __init__(self, input_dict):
        self.OBtype = 'SEQ_Darks'
        self.Object = OBProperty('Object', input_dict.get('Object', ''), str)
        self.nExp = OBProperty('nExp', input_dict.get('nExp', 1), int)
        self.ExpTime = OBProperty('ExpTime', input_dict.get('ExpTime', 1), float)

    def to_lines(self):
        self.lines = []
        self.lines += [f" - Object: {self.get('Object')}"]
        self.lines += [f"   nExp: {self.get('nExp')}"]
        self.lines += [f"   ExpTime: {self.get('ExpTime')}"]
        return self.lines


class SEQ_Calibrations(BaseOB):
    def __init__(self, input_dict):
        self.OBtype = 'SEQ_Calibrations'
        self.Object = OBProperty('Object', input_dict.get('Object', ''), str)
        self.CalSource = OBProperty('CalSource', input_dict.get('CalSource', 'EtalonFiber'), str)
        self.CalND1 = OBProperty('CalND1', input_dict.get('CalND1', 'OD 0.1'), str)
        self.CalND2 = OBProperty('CalND2', input_dict.get('CalND2', 'OD 0.1'), str)
        self.nExp = OBProperty('nExp', input_dict.get('nExp', 1), int)
        self.ExpTime = OBProperty('ExpTime', input_dict.get('ExpTime', 1), float)
        self.SSS_Science = OBProperty('SSS_Science', input_dict.get('SSS_Science', True), bool)
        self.SSS_Sky = OBProperty('SSS_Sky', input_dict.get('SSS_Sky', True), bool)
        self.TakeSimulCal = OBProperty('TakeSimulCal', input_dict.get('TakeSimulCal', True), bool)
        self.ExpMeterExpTime = OBProperty('ExpMeterExpTime', input_dict.get('ExpMeterExpTime', 1), float)
        self.FF_FiberPos = OBProperty('FF_FiberPos', input_dict.get('FF_FiberPos', 'Blank'), str)

    def to_lines(self):
        self.lines = []
        self.lines += [f" - Object: {self.get('Object')}"]
        self.lines += [f"   CalSource: {self.get('CalSource')}"]
        self.lines += [f"   CalND1: {self.get('CalND1')}"]
        self.lines += [f"   CalND2: {self.get('CalND2')}"]
        self.lines += [f"   nExp: {self.get('nExp')}"]
        self.lines += [f"   ExpTime: {self.get('ExpTime')}"]
        self.lines += [f"   SSS_Science: {self.get('SSS_Science')}"]
        self.lines += [f"   SSS_Sky: {self.get('SSS_Sky')}"]
        self.lines += [f"   TakeSimulCal: {self.get('TakeSimulCal')}"]
        self.lines += [f"   ExpMeterExpTime: {self.get('ExpMeterExpTime')}"]
        self.lines += [f"   FF_FiberPos: {self.get('FF_FiberPos')}"]
        return self.lines


class ScienceOB(BaseOB):
    def __init__(self, OBdict):
        super().__init__()
        self.OBtype = 'kpf_sci'
        self.OBversion = '0.6'
        self.star_list_line = ''
        # Properties
        self.TargetName = OBProperty('TargetName', OBdict.get('TargetName', ''), str)
        self.GaiaID = OBProperty('GaiaID', OBdict.get('GaiaID', ''), str)
        self.twoMASSID = OBProperty('2MASSID', OBdict.get('2MASSID', ''), str)
        self.Parallax = OBProperty('Parallax', OBdict.get('Parallax', 0), float)
        self.RadialVelocity = OBProperty('RadialVelocity', OBdict.get('RadialVelocity', 0), float)
        self.Gmag = OBProperty('Gmag', OBdict.get('Gmag', ''), str)
        self.Jmag = OBProperty('Jmag', OBdict.get('Jmag', ''), str)
        self.Teff = OBProperty('Teff', OBdict.get('Teff', 0), float)
        self.GuideMode = OBProperty('GuideMode', OBdict.get('GuideMode', 'auto'), str)
        self.GuideCamGain = OBProperty('GuideCamGain', OBdict.get('GuideCamGain', 'high'), str)
        self.GuideFPS = OBProperty('GuideFPS', OBdict.get('GuideFPS', 100), float)
        self.TriggerCaHK = OBProperty('TriggerCaHK', OBdict.get('TriggerCaHK', True), bool)
        self.TriggerGreen = OBProperty('TriggerGreen', OBdict.get('TriggerGreen', True), bool)
        self.TriggerRed = OBProperty('TriggerRed', OBdict.get('TriggerRed', True), bool)
        self.SEQ_Observations = SEQ_Observations(OBdict.get('SEQ_Observations', {}))

    def to_lines(self):
        self.lines = [f"Template_Name: {self.OBtype}"]
        self.lines += [f"Template_Version: {self.OBversion}"]
        self.lines += [f""]
        self.lines += [f"# Target Info"]
        self.lines += [f"TargetName: {self.get('TargetName')}"]
        self.lines += [f"GaiaID: {self.get('GaiaID')}"]
        self.lines += [f"2MASSID: {self.get('twoMASSID')}"]
        self.lines += [f"Parallax: {self.get('Parallax')}"]
        self.lines += [f"RadialVelocity: {self.get('RadialVelocity')}"]
        self.lines += [f"Gmag: {self.get('Gmag')}"]
        self.lines += [f"Jmag: {self.get('Jmag')}"]
        self.lines += [f"Teff: {self.get('Teff')}"]
        self.lines += [f""]
        self.lines += [f"# Guider Setup"]
        self.lines += [f"GuideMode: {self.get('GuideMode')}"]
        if self.get('GuideMode') != 'auto':
            self.lines += [f"GuideCamGain: {self.get('GuideCamGain')}"]
            self.lines += [f"GuideFPS: {self.get('GuideFPS')}"]
        self.lines += [f""]
        self.lines += [f"# Spectrograph Setup"]
        self.lines += [f"TriggerCaHK: {self.get('TriggerCaHK')}"]
        self.lines += [f"TriggerGreen: {self.get('TriggerGreen')}"]
        self.lines += [f"TriggerRed: {self.get('TriggerRed')}"]
        self.lines += [f"# Observations"]
        self.lines += [f"SEQ_Observations:"]
        self.lines.extend(self.SEQ_Observations.to_lines())
        if len(self.star_list_line) > 0:
            self.lines += [f""]
            self.lines += [f"star_list_line: {self.star_list_line}"]


class CalibrationOB(BaseOB):
    def __init__(self, OBdict):
        super().__init__()
        self.OBtype = 'kpf_cal'
        self.OBversion = '0.6'
        self.TriggerCaHK = OBProperty('TriggerCaHK', OBdict.get('TriggerCaHK', True), bool)
        self.TriggerGreen = OBProperty('TriggerGreen', OBdict.get('TriggerGreen', True), bool)
        self.TriggerRed = OBProperty('TriggerRed', OBdict.get('TriggerRed', True), bool)
        self.TriggerExpMeter = OBProperty('TriggerExpMeter', OBdict.get('TriggerExpMeter', False), bool)
        self.SEQ_Darks1 = SEQ_Darks(OBdict.get('SEQ_Darks', [{}, {}])[0])
        self.SEQ_Darks2 = SEQ_Darks(OBdict.get('SEQ_Darks', [{}, {}])[1])
        self.SEQ_Calibrations = SEQ_Darks(OBdict.get('SEQ_Calibrations', {}))

    def to_lines(self):
        self.lines = [f"Template_Name: {self.OBtype}"]
        self.lines += [f"Template_Version: {self.OBversion}"]
        self.lines += [f""]
        self.lines += [f"TriggerCaHK: {self.get('TriggerCaHK')}"]
        self.lines += [f"TriggerGreen: {self.get('TriggerGreen')}"]
        self.lines += [f"TriggerRed: {self.get('TriggerRed')}"]
        self.lines += [f"TriggerExpMeter: {self.get('TriggerExpMeter')}"]
        self.lines += [f""]
        self.lines += [f"# Darks"]
        self.lines += [f"SEQ_Darks:"]
        self.lines.extend(self.SEQ_Darks1.to_lines())
        self.lines.extend(self.SEQ_Darks2.to_lines())
        self.lines += [f"# Calibrations"]
        self.lines += [f"SEQ_Calibrations:"]
        self.lines.extend(self.SEQ_Calibrations.to_lines())
