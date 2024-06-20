from pathlib import Path
import yaml


##-------------------------------------------------------------------------
## OB Data Model Components
##-------------------------------------------------------------------------
class OBProperty(object):
    def __init__(self, name, value, valuetype):
        self.name = name
        self.value = valuetype(value)
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
        if name == '2MASSID':
            name = 'twoMASSID'
        try:
            thisOBproperty = getattr(self, name)
            thisOBproperty.set(value)
        except AttributeError as e:
            print(f"AttributeError setting {name}. skipping")

    @classmethod
    def load_from_file(self, fname):
        try:
            with open(fname, 'r') as f:
                OBdict = yaml.safe_load(f)
            if OBdict.get('Template_Name', None) == 'kpf_sci':
                OB = ScienceOB(OBdict)
                if OBdict.get('star_list_line', None) is not None:
                    OB.star_list_line = OBdict.get('star_list_line')
                else:
                    OB.star_list_line = ''
            elif OBdict.get('Template_Name', None) == 'kpf_cal':
                OB = CalibrationOB(OBdict)
            OB.to_lines()
        except Exception as e:
            OB = None
        return OB

    def to_lines():
        pass

    def write_to_file(self, file):
        file = Path(file)
        if file.parent.exists() is False:
            file.parent.mkdir(mode=0o777, parents=True)
        if file.exists() is True: file.unlink()
        with open(file, 'w') as f:
            for line in self.to_lines():
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

##-------------------------------------------------------------------------
## Science OB Components
##-------------------------------------------------------------------------
class SEQ_Observations(BaseOB):
    def __init__(self, input_dict):
        super().__init__()
        self.OBtype = 'SEQ_Observations'
        self.Object = OBProperty('Object', input_dict.get('Object', ''), str)
        self.nExp = OBProperty('nExp', input_dict.get('nExp', 1), int)
        self.ExpTime = OBProperty('ExpTime', input_dict.get('ExpTime', 1), float)
        self.ExpMeterMode = OBProperty('ExpMeterMode', input_dict.get('ExpMeterMode', 'monitor'), str)
        self.ExpMeterExpTime = OBProperty('ExpMeterExpTime', input_dict.get('ExpMeterExpTime', 1), float)
        self.AutoExpMeter = OBProperty('AutoExpMeter', input_dict.get('AutoExpMeter', False), bool)
        self.ExpMeterBin = OBProperty('ExpMeterBin', input_dict.get('ExpMeterBin', '710.625'), str)
        self.ExpMeterThreshold = OBProperty('ExpMeterThreshold', input_dict.get('ExpMeterThreshold', 50000), float)
        self.TakeSimulCal = OBProperty('TakeSimulCal', input_dict.get('TakeSimulCal', True), bool)
        self.AutoNDFilters = OBProperty('AutoNDFilters', input_dict.get('AutoNDFilters', False), bool)
        self.CalND1 = OBProperty('CalND1', input_dict.get('CalND1', 'OD 0.1'), str)
        self.CalND2 = OBProperty('CalND2', input_dict.get('CalND2', 'OD 0.1'), str)
        self.to_lines()

    def to_lines(self):
        self.lines = []
        self.lines += [f" - Object: {self.get('Object')}"]
        self.lines += [f"   nExp: {self.get('nExp')}"]
        self.lines += [f"   ExpTime: {self.get('ExpTime')}"]
        self.lines += [f"   ExpMeterMode: {self.get('ExpMeterMode')}"]
        self.lines += [f"   AutoExpMeter: {self.get('AutoExpMeter')}"]
        if not self.get('AutoExpMeter'):
            self.lines += [f"   ExpMeterExpTime: {self.get('ExpMeterExpTime')}"]
        if self.get('ExpMeterMode') == 'control':
            self.lines += [f"   ExpMeterBin: {self.get('ExpMeterBin')}"]
            self.lines += [f"   ExpMeterThreshold: {self.get('ExpMeterThreshold')}"]
        self.lines += [f"   TakeSimulCal: {self.get('TakeSimulCal')}"]
        if self.get('TakeSimulCal'):
            self.lines += [f"   AutoNDFilters: {self.get('AutoNDFilters')}"]
            if not self.get('AutoNDFilters'):
                self.lines += [f"   CalND1: {self.get('CalND1')}"]
                self.lines += [f"   CalND2: {self.get('CalND2')}"]
        return self.lines

    def to_dict(self):
        seqdict = {'Object': self.get('Object'),
                   'nExp': self.get('nExp'),
                   'ExpTime': self.get('ExpTime'),
                   'ExpMeterMode': self.get('ExpMeterMode'),
                   'AutoExpMeter': self.get('AutoExpMeter'),
                   'ExpMeterExpTime': self.get('ExpMeterExpTime'),
                   'ExpMeterBin': self.get('ExpMeterBin'),
                   'ExpMeterThreshold': self.get('ExpMeterThreshold'),
                   'TakeSimulCal': self.get('TakeSimulCal'),
                   'AutoNDFilters': self.get('AutoNDFilters'),
                   'CalND1': self.get('CalND1'),
                   'CalND2': self.get('CalND2'),
                   }
        return seqdict


class ScienceOB(BaseOB):
    def __init__(self, OBdict):
        super().__init__()
        self.OBtype = 'kpf_sci'
        self.OBversion = '1.0'
        self.star_list_line = ''
        # Properties
        self.TargetName = OBProperty('TargetName', OBdict.get('TargetName', ''), str)
        self.GaiaID = OBProperty('GaiaID', OBdict.get('GaiaID', ''), str)
        self.twoMASSID = OBProperty('2MASSID', OBdict.get('2MASSID', ''), str)
        self.Parallax = OBProperty('Parallax', OBdict.get('Parallax', 0.), float)
        self.RadialVelocity = OBProperty('RadialVelocity', OBdict.get('RadialVelocity', 0), float)
        self.Gmag = OBProperty('Gmag', OBdict.get('Gmag', ''), str)
        self.Jmag = OBProperty('Jmag', OBdict.get('Jmag', ''), str)
        self.Teff = OBProperty('Teff', OBdict.get('Teff', 0), float)
        self.TriggerCaHK = OBProperty('TriggerCaHK', OBdict.get('TriggerCaHK', True), bool)
        self.TriggerGreen = OBProperty('TriggerGreen', OBdict.get('TriggerGreen', True), bool)
        self.TriggerRed = OBProperty('TriggerRed', OBdict.get('TriggerRed', True), bool)
        self.BlockSky = OBProperty('BlockSky', OBdict.get('BlockSky', False), bool)
        self.SEQ_Observations1 = None
        observations = OBdict.get('SEQ_Observations', [])
        for observation in observations:
            try:
                this_observation = SEQ_Observations(observation)
            except:
                this_observation = None
            if this_observation is not None:
                if self.SEQ_Observations1 == None:
                    self.SEQ_Observations1 = this_observation
        self.to_lines()

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
        self.lines += [f"# Spectrograph Setup"]
        self.lines += [f"TriggerCaHK: {self.get('TriggerCaHK')}"]
        self.lines += [f"TriggerGreen: {self.get('TriggerGreen')}"]
        self.lines += [f"TriggerRed: {self.get('TriggerRed')}"]
        self.lines += [f"BlockSky: {self.get('BlockSky')}"]
        if self.SEQ_Observations1 is not None:
            self.lines += [f"# Observations"]
            self.lines += [f"SEQ_Observations:"]
            self.lines.extend(self.SEQ_Observations1.to_lines())

        if len(self.star_list_line) > 0:
            self.lines += [f""]
            self.lines += [f"star_list_line: {self.star_list_line}"]
        return self.lines

    def to_dict(self):
        OBdict = {'Template_Name': self.OBtype,
                  'Template_Version': self.OBversion,
                  'TargetName': self.get('TargetName'),
                  'GaiaID': self.get('GaiaID'),
                  '2MASSID': self.get('twoMASSID'),
                  'Parallax': self.get('Parallax'),
                  'RadialVelocity': self.get('RadialVelocity'),
                  'Gmag': self.get('Gmag'),
                  'Jmag': self.get('Jmag'),
                  'Teff': self.get('Teff'),
                  'TriggerCaHK': self.get('TriggerCaHK'),
                  'TriggerGreen': self.get('TriggerGreen'),
                  'TriggerRed': self.get('TriggerRed'),
                  'BlockSky': self.get('BlockSky'),
                 }
        if self.SEQ_Observations1 is not None:
            OBdict['SEQ_Observations'] = [self.SEQ_Observations1.to_dict()]
        return OBdict


##-------------------------------------------------------------------------
## Calibration OB Components
##-------------------------------------------------------------------------
class SEQ_Darks(BaseOB):
    def __init__(self, input_dict):
        super().__init__()
        self.OBtype = 'SEQ_Darks'
        self.Object = OBProperty('Object', input_dict.get('Object', ''), str)
        self.nExp = OBProperty('nExp', input_dict.get('nExp', 1), int)
        self.ExpTime = OBProperty('ExpTime', input_dict.get('ExpTime', 1), float)
        self.to_lines()

    def to_lines(self):
        self.lines = []
        self.lines += [f" - Object: {self.get('Object')}"]
        self.lines += [f"   nExp: {self.get('nExp')}"]
        self.lines += [f"   ExpTime: {self.get('ExpTime')}"]
        return self.lines

    def to_dict(self):
        seqdict = {'Object': self.get('Object'),
                   'nExp': self.get('nExp'),
                   'ExpTime': self.get('ExpTime'),
                   }
        return seqdict


class SEQ_Calibrations(BaseOB):
    def __init__(self, input_dict):
        super().__init__()
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
        self.ExpMeterMode = OBProperty('ExpMeterMode', input_dict.get('ExpMeterMode', 'monitor'), str)
        self.ExpMeterExpTime = OBProperty('ExpMeterExpTime', input_dict.get('ExpMeterExpTime', 1), float)
        self.ExpMeterBin = OBProperty('ExpMeterBin', input_dict.get('ExpMeterBin', '710.625'), str)
        self.ExpMeterThreshold = OBProperty('ExpMeterThreshold', input_dict.get('ExpMeterThreshold', 50000), float)
        self.FF_FiberPos = OBProperty('FF_FiberPos', input_dict.get('FF_FiberPos', 'Blank'), str)
        self.to_lines()

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
        self.lines += [f"   ExpMeterMode: {self.get('ExpMeterMode')}"]
        self.lines += [f"   ExpMeterExpTime: {self.get('ExpMeterExpTime')}"]
        if self.get('ExpMeterMode') == 'control':
            self.lines += [f"   ExpMeterBin: {self.get('ExpMeterBin')}"]
            self.lines += [f"   ExpMeterThreshold: {self.get('ExpMeterThreshold')}"]
        self.lines += [f"   FF_FiberPos: {self.get('FF_FiberPos')}"]
        return self.lines

    def to_dict(self):
        seqdict = {'Object': self.get('Object'),
                   'CalSource': self.get('CalSource'),
                   'CalND1': self.get('CalND1'),
                   'CalND2': self.get('CalND2'),
                   'nExp': self.get('nExp'),
                   'ExpTime': self.get('ExpTime'),
                   'SSS_Science': self.get('SSS_Science'),
                   'SSS_Sky': self.get('SSS_Sky'),
                   'TakeSimulCal': self.get('TakeSimulCal'),
                   'ExpMeterMode': self.get('ExpMeterMode'),
                   'ExpMeterExpTime': self.get('ExpMeterExpTime'),
                   'ExpMeterBin': self.get('ExpMeterBin'),
                   'ExpMeterThreshold': self.get('ExpMeterThreshold'),
                   'FF_FiberPos': self.get('FF_FiberPos'),
                   }
        return seqdict


class CalibrationOB(BaseOB):
    def __init__(self, OBdict):
        super().__init__()
        self.OBtype = 'kpf_cal'
        self.OBversion = '1.0'
        self.TriggerCaHK = OBProperty('TriggerCaHK', OBdict.get('TriggerCaHK', True), bool)
        self.TriggerGreen = OBProperty('TriggerGreen', OBdict.get('TriggerGreen', True), bool)
        self.TriggerRed = OBProperty('TriggerRed', OBdict.get('TriggerRed', True), bool)
        # SEQ_Darks
        self.SEQ_Darks1 = None
        self.SEQ_Darks2 = None
        dark_list = OBdict.get('SEQ_Darks', [])
        for entry in dark_list:
            try:
                this_dark = SEQ_Darks(entry)
            except:
                this_dark = None
            if this_dark is not None:
                if self.SEQ_Darks1 == None:
                    self.SEQ_Darks1 = this_dark
                elif self.SEQ_Darks2 == None:
                    self.SEQ_Darks2 = this_dark
        # SEQ_Calibrations
        self.SEQ_Calibrations1 = None
        self.SEQ_Calibrations2 = None
        seq_list = OBdict.get('SEQ_Calibrations', [])
        for entry in seq_list:
            try:
                this_cal = SEQ_Calibrations(entry)
            except:
                this_cal = None
            if this_cal is not None:
                if self.SEQ_Calibrations1 == None:
                    self.SEQ_Calibrations1 = this_cal
                elif self.SEQ_Calibrations2 == None:
                    self.SEQ_Calibrations2 = this_cal
        # Render lines
        self.to_lines()

    def to_lines(self):
        self.lines = [f"Template_Name: {self.OBtype}"]
        self.lines += [f"Template_Version: {self.OBversion}"]
        self.lines += [f""]
        self.lines += [f"TriggerCaHK: {self.get('TriggerCaHK')}"]
        self.lines += [f"TriggerGreen: {self.get('TriggerGreen')}"]
        self.lines += [f"TriggerRed: {self.get('TriggerRed')}"]
        self.lines += [f""]

        if self.SEQ_Darks1 is not None or self.SEQ_Darks2 is not None:
            self.lines += [f"# Darks"]
            self.lines += [f"SEQ_Darks:"]
        if self.SEQ_Darks1 is not None:
            self.lines.extend(self.SEQ_Darks1.to_lines())
        if self.SEQ_Darks2 is not None:
            self.lines.extend(self.SEQ_Darks2.to_lines())
        if self.SEQ_Calibrations1 is not None or self.SEQ_Calibrations2 is not None:
            self.lines += [f"# Calibrations"]
            self.lines += [f"SEQ_Calibrations:"]
        if self.SEQ_Calibrations1 is not None:
            self.lines.extend(self.SEQ_Calibrations1.to_lines())
        if self.SEQ_Calibrations2 is not None:
            self.lines.extend(self.SEQ_Calibrations2.to_lines())
        return self.lines

    def to_dict(self):
        OBdict = {'Template_Name': self.OBtype,
                  'Template_Version': self.OBversion,
                  'TriggerCaHK': self.get('TriggerCaHK'),
                  'TriggerGreen': self.get('TriggerGreen'),
                  'TriggerRed': self.get('TriggerRed'),
                 }
        if self.SEQ_Darks1 is not None and self.SEQ_Darks2 is None:
            OBdict['SEQ_Darks'] = [self.SEQ_Darks1.to_dict()]
        elif self.SEQ_Darks1 is not None and self.SEQ_Darks2 is not None:
            OBdict['SEQ_Darks'] = [self.SEQ_Darks1.to_dict(),
                                   self.SEQ_Darks2.to_dict()]
        elif self.SEQ_Darks1 is None and self.SEQ_Darks2 is not None:
            OBdict['SEQ_Darks'] = [self.SEQ_Darks2.to_dict()]

        if self.SEQ_Calibrations1 is not None and self.SEQ_Calibrations2 is None:
            OBdict['SEQ_Calibrations'] = [self.SEQ_Calibrations1.to_dict()]
        elif self.SEQ_Calibrations1 is not None and self.SEQ_Calibrations1 is not None:
            OBdict['SEQ_Calibrations'] = [self.SEQ_Calibrations1.to_dict(),
                                          self.SEQ_Calibrations2.to_dict()]
        elif self.SEQ_Calibrations1 is None and self.SEQ_Calibrations2 is not None:
            OBdict['SEQ_Calibrations'] = [self.SEQ_Calibrations2.to_dict()]

        return OBdict

        