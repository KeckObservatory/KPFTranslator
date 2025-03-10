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
        skip_if_dark = ['IntensityMonitor', 'CalND1', 'CalND2',
                        'OpenScienceShutter', 'OpenSkyShutter',
                        'TakeSimulCal', 'WideFlatPos', 'ExpMeterMode',
                        'ExpMeterExpTime', 'ExpMeterBin',
                        'ExpMeterThreshold']
        self.pruning_guide = [(self.get('CalSource').lower() in ['dark', 'home'], skip_if_dark),
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