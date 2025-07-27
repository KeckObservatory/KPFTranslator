from pathlib import Path
import yaml

from kpf.ObservingBlocks import BaseOBComponent

try:
    import ktl
except ModuleNotFoundError:
    ktl = None


class Calibration(BaseOBComponent):
    def __init__(self, input_dict):
        properties_file = Path(__file__).parent / 'CalibrationProperties.yaml'
        with open(properties_file, 'r') as f:
            properties = yaml.safe_load(f.read())
        super().__init__('Calibration', '2.0', properties=properties)
        self.list_element = True
        self.calsources = ['Dark', 'Home', 'dark', 'WideFlat', 'BrdbandFiber',
                           'U_gold', 'U_daily', 'Th_daily', 'Th_gold',
                           'LFCFiber', 'EtalonFiber',
                           'SoCal-CalFib', 'SoCal-SciSky']
        try:
            WAVEBINS = ktl.cache('kpf_expmeter', 'WAVEBINS')
            self.expmeter_bands = [f"{float(b):.0f}nm" for b in WAVEBINS.read().split()]
            ND1POS = ktl.cache('kpfcal', 'ND1POS')
            ND2POS = ktl.cache('kpfcal', 'ND2POS')
            self.ND_values = {'CalND1': list(ND1POS._getEnumerators()),
                              'CalND2': list(ND2POS._getEnumerators())}
            for nd in ['CalND1', 'CalND2']:
                if 'Unknown' in self.ND_values[nd]:
                    self.ND_values[nd].pop(self.ND_values[nd].index('Unknown'))
        except:
            self.expmeter_bands = [f"{float(b):.0f}nm" for b in [498.12, 604.38, 710.62, 816.88]]
            self.ND_values = {'CalND1': ['OD 0.1', 'OD 1.0', 'OD 1.3', 'OD 2.0', 'OD 3.0', 'OD 4.0'],
                              'CalND2': ['OD 0.1', 'OD 0.3', 'OD 0.5', 'OD 0.8', 'OD 1.0', 'OD 4.0']}
        self.skip_if_dark = ['IntensityMonitor', 'CalND1', 'CalND2',
                             'OpenScienceShutter', 'OpenSkyShutter',
                             'TakeSimulCal', 'WideFlatPos', 'ExpMeterMode',
                             'ExpMeterExpTime', 'ExpMeterBin',
                             'ExpMeterThreshold']
        # Handle different defaults for dark frame
        if input_dict.get('CalSource') in ['Dark', 'dark', 'Home', 'home']:
            if 'IntensityMonitor' not in input_dict.keys():
                input_dict['IntensityMonitor'] = False
            if 'OpenScienceShutter' not in input_dict.keys():
                input_dict['OpenScienceShutter'] = False
            if 'OpenSkyShutter' not in input_dict.keys():
                input_dict['OpenSkyShutter'] = False
            if 'TakeSimulCal' not in input_dict.keys():
                input_dict['TakeSimulCal'] = False
            if 'WideFlatPos' not in input_dict.keys():
                input_dict['WideFlatPos'] = 'Blank'
            if 'ExpMeterMode' not in input_dict.keys():
                input_dict['ExpMeterMode'] = 'off'
        self.from_dict(input_dict)


    def get_pruning_guide(self):
        return [(self.get('CalSource').lower() in ['dark', 'home'], self.skip_if_dark),
                (self.get('ExpMeterMode') in ['off', 'False', False], ['ExpMeterExpTime']),
                (self.get('ExpMeterMode') != 'control', ['ExpMeterBin', 'ExpMeterThreshold']),
                (self.get('TakeSimulCal') == False, ['CalND1', 'CalND2']),
                (self.get('CalSource') != 'WideFlat', ['WideFlatPos'])
                ]


    def check_property(self, pname):
        if pname in self.skip_if_dark:
            if self.get('CalSource').lower() in ['dark', 'home']:
                return False, ' # Unused: CalSource = Dark'
        if pname == 'CalSource':
            if self.get(pname) not in self.calsources:
                return True, ' # ERROR: CalSource invalid'
        elif pname == 'Object':
            if self.get(pname) in ['', None]:
                return True, ' # ERROR: Object is empty'
        elif pname  == 'ExpMeterExpTime':
            if self.get('ExpMeterMode') in [False, 'False', 'Off', 'off']:
                return False, ' # Unused: ExpMeterMode == off'
        elif pname == 'ExpMeterBin':
            if self.get(pname) not in [1, 2, 3, 4]:
                return True, ' # ERROR: ExpMeterBin must be 1, 2, 3, or 4'
            elif self.get('ExpMeterMode') != 'control':
                return False, ' # Unused: ExpMeterMode != control'
        elif pname == 'ExpMeterThreshold':
            if self.get(pname) < 0:
                return True, ' # ERROR: ExpMeterThreshold < 0'
            elif self.get('ExpMeterMode') != 'control':
                return False, ' # Unused: ExpMeterMode != control'
        elif pname in ['CalND1', 'CalND2']:
            if self.get(pname) not in self.ND_values[pname]:
                return True, f' # ERROR: {pname} invalid'
        return False, ''


    def add_comment(self, pname):
        error, comment = self.check_property(pname)
        return comment


    def validate(self):
        '''
        '''
        valid = True
        for p in self.properties:
            error, comment = self.check_property(p['name'])
            if error == True:
                valid = False
        return valid


    def __str__(self):
        if self.CalSource.value == 'EtalonFiber':
            calsource = 'Etalon'
        elif self.CalSource.value.lower() in ['dark', 'home']:
            calsource = 'Dark'
        else:
            calsource = self.CalSource.value
        return f"{calsource}:{self.nExp.value:d}x{self.ExpTime.value:.0f}s"


    def summary(self):
        return self.__str__()