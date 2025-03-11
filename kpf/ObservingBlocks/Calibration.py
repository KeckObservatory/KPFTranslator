from pathlib import Path
import yaml

from kpf.ObservingBlocks import BaseOBComponent


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
        self.skip_if_dark = ['IntensityMonitor', 'CalND1', 'CalND2',
                             'OpenScienceShutter', 'OpenSkyShutter',
                             'TakeSimulCal', 'WideFlatPos', 'ExpMeterMode',
                             'ExpMeterExpTime', 'ExpMeterBin',
                             'ExpMeterThreshold']
        self.pruning_guide = [(self.get('CalSource').lower() in ['dark', 'home'], self.skip_if_dark),
                              (self.get('ExpMeterMode') in ['off', 'False', False], ['ExpMeterExpTime']),
                              (self.get('ExpMeterMode') != 'control', ['ExpMeterBin', 'ExpMeterThreshold']),
                              (self.get('TakeSimulCal') == False, ['CalND1', 'CalND2']),
                              (self.get('CalSource') != 'WideFlat', ['WideFlatPos'])
                              ]
        self.from_dict(input_dict)


    def validate(self):
        '''
        '''
        valid = True
        for p in self.properties:
            if self.get(p['name']) is None:
                print(f"ERROR: {p['name']} is undefined, default is {p['defaultvalue']}")
                valid = False
        # CalSource is not allowed value
        if self.get('CalSource') not in self.calsources:
            print(f"ERROR: CalSource invalid")
            valid = False
        # Check if Object is empty
        if self.get('Object') in ['', None]:
            print(f"ERROR: Object field is empty")
            valid = False
        return valid


    def add_comment(self, pname):
        # CalSource is not allowed value
        if self.get('CalSource') not in self.calsources:
            if pname in ['CalSource']:
                return ' # ERROR: CalSource invalid'
        # Object is empty
        if self.get('Object') in ['', None]:
            if pname in ['Object']:
                return ' # ERROR: Object field is empty'
        # CalSource is dark
        if self.get('CalSource').lower() in ['dark', 'home']:
            if pname in self.skip_if_dark:
                return ' # Unused: CalSource == Dark'
        # TakeSimulcal is false
        if self.get('TakeSimulCal') == False:
            if pname in ['CalND2']:
                return ' # Unused: TakeSimulCal == False'
        return ''


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