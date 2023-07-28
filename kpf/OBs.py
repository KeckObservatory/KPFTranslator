from pathlib import Path
import yaml


##-------------------------------------------------------------------------
## OB Data Model
##-------------------------------------------------------------------------
class BaseOB(object):
    def __init__(self, OBdict):
        if isinstance(OBdict, dict):
            self.OBdict = OBdict
        else:
            self.OBdict = {}
        self.lines = []
        self.OBtype = None
        self.OBversion = None

    def get(self, *args):
        return self.OBdict.get(*args)

    def set(self, keyword, value, seq=None, seqindex=0):
        if seq==None:
            self.OBdict[keyword] = value
        else:
            if self.OBdict.get(seq, None) is None:
                self.OBdict[seq] = [{}]
            if len(self.OBdict.get(seq)) < seqindex-1:
                self.OBdict[seq].append({})
            self.OBdict[seq][seqindex][keyword] = value
        self.to_lines()

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
        except Exception as e:
            pass
        OB.to_lines()
        return OB

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


class ScienceOB(BaseOB):
    def __init__(self, OBdict):
        super().__init__(OBdict)
        self.OBtype = 'kpf_sci'
        self.OBversion = '0.6'
        self.star_list_line = ''

    def to_lines(self):
        self.lines = [f"Template_Name: {self.OBtype}"]
        self.lines += [f"Template_Version: {self.OBversion}"]
        self.lines += [f""]
        self.lines += [f"# Target Info"]
        self.lines += [f"TargetName: {self.OBdict.get('TargetName', '')}"]
        self.lines += [f"GaiaID: {self.OBdict.get('GaiaID', '')}"]
        self.lines += [f"2MASSID: {self.OBdict.get('2MASSID', '')}"]
        if self.OBdict.get('Parallax', None) is not None:
            self.lines += [f"Parallax: {self.OBdict.get('Parallax')}"]
        if self.OBdict.get('RadialVelocity', None) is not None:
            self.lines += [f"RadialVelocity: {self.OBdict.get('RadialVelocity')}"]
        self.lines += [f"Gmag: {self.OBdict.get('Gmag', '')}"]
        self.lines += [f"Jmag: {self.OBdict.get('Jmag', '')}"]
        if self.OBdict.get('Teff', None) is not None:
            self.lines += [f"Teff: {self.OBdict.get('Teff')}"]
        self.lines += [f""]
        self.lines += [f"# Guider Setup"]
        self.lines += [f"GuideMode: {self.OBdict.get('GuideMode', 'auto')}"]
        if self.OBdict.get('GuideMode', None) != 'auto':
            self.lines += [f"GuideCamGain: {self.OBdict.get('GuideCamGain', 'high')}"]
            self.lines += [f"GuideFPS: {self.OBdict.get('GuideFPS', '100')}"]
        self.lines += [f""]
        self.lines += [f"# Spectrograph Setup"]
        self.lines += [f"TriggerCaHK: {self.OBdict.get('TriggerCaHK', 'True')}"]
        self.lines += [f"TriggerGreen: {self.OBdict.get('TriggerGreen', 'True')}"]
        self.lines += [f"TriggerRed: {self.OBdict.get('TriggerRed', 'True')}"]
        if len(self.OBdict.get('SEQ_Observations', [])) > 0:
            seq = self.OBdict.get('SEQ_Observations')[0]
            self.lines += [f""]
            self.lines += [f"# Observations"]
            self.lines += [f"SEQ_Observations:"]
            self.lines += [f" - Object: {seq.get('Object', '')}"]
            self.lines += [f"   nExp: {seq.get('nExp', 1)}"]
            self.lines += [f"   ExpTime: {seq.get('ExpTime', 1)}"]
            self.lines += [f"   ExpMeterMode: {seq.get('ExpMeterMode', 'monitor')}"]
            self.lines += [f"   AutoExpMeter: {seq.get('AutoExpMeter', 'False')}"]
            if seq.get('AutoExpMeter', False) not in [True, 'True']:
                self.lines += [f"   ExpMeterExpTime: {seq.get('ExpMeterExpTime', '1')}"]
            self.lines += [f"   TakeSimulCal: {seq.get('TakeSimulCal', 'True')}"]
            if seq.get('TakeSimulCal', None) in [True, 'True']:
                if seq.get('AutoNDFilters', None) is not None:
                    self.lines += [f"   AutoNDFilters: {seq.get('AutoNDFilters', 'False')}"]
                if seq.get('AutoNDFilters', None) not in [True, 'True']:
                    self.lines += [f"   CalND1: {seq.get('CalND1', 'OD 0.1')}"]
                    self.lines += [f"   CalND2: {seq.get('CalND2', 'OD 0.1')}"]
        if len(self.star_list_line) > 0:
            self.lines += [f""]
            self.lines += [f"star_list_line: {self.star_list_line}"]


class CalibrationOB(BaseOB):
    def __init__(self, OBdict):
        super().__init__(OBdict)
        self.OBtype = 'kpf_cal'
        self.OBversion = '0.6'

    def to_lines(self):
        self.lines = [f"Template_Name: {self.OBtype}"]
        self.lines += [f"Template_Version: {self.OBversion}"]
        self.lines += [f""]
        self.lines += [f"TriggerCaHK: {self.OBdict.get('TriggerCaHK', True)}"]
        self.lines += [f"TriggerGreen: {self.OBdict.get('TriggerGreen', True)}"]
        self.lines += [f"TriggerRed: {self.OBdict.get('TriggerRed', True)}"]
        self.lines += [f"TriggerExpMeter: {self.OBdict.get('TriggerExpMeter', False)}"]
        self.lines += [f""]
        if len(self.OBdict.get('SEQ_Darks', [])) > 0:
            self.lines += [f"# Darks"]
            self.lines += [f"SEQ_Darks:"]
            for darkseq in self.OBdict.get('SEQ_Darks'):
                self.lines += [f"- Object: {darkseq.get('Object', '')}"]
                self.lines += [f"  nExp: {darkseq.get('nExp', 1)}"]
                self.lines += [f"  ExpTime: {darkseq.get('ExpTime', 0)}"]
        if len(self.OBdict.get('SEQ_Calibrations', [])) > 0:
            self.lines += [f"# Lamp Calibrations"]
            self.lines += [f"SEQ_Calibrations:"]
            for calseq in self.OBdict.get('SEQ_Calibrations'):
                self.lines += [f"- CalSource: {calseq.get('CalSource', 'EtalonFiber')}"]
                self.lines += [f"  Object: {calseq.get('Object', '')}"]
                self.lines += [f"  CalND1: {calseq.get('CalND1', 'OD 0.1')}"]
                self.lines += [f"  CalND2: {calseq.get('CalND2', 'OD 0.1')}"]
                self.lines += [f"  nExp: {calseq.get('nExp', 1)}"]
                self.lines += [f"  ExpTime: {calseq.get('ExpTime', 1)}"]
                self.lines += [f"  SSS_Science: {calseq.get('SSS_Science', True)}"]
                self.lines += [f"  SSS_Sky: {calseq.get('SSS_Sky', True)}"]
                self.lines += [f"  TakeSimulCal: {calseq.get('TakeSimulCal', True)}"]
                self.lines += [f"  FF_FiberPos: {calseq.get('FF_FiberPos', 'Blank')}"]
                self.lines += [f"  ExpMeterExpTime: {calseq.get('ExpMeterExpTime', 1)}"]
