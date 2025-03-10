from pathlib import Path
import yaml

try:
    import ktl
except:
    ktl = None
from kpf.ObservingBlocks import BaseOBComponent


class Observation(BaseOBComponent):
    def __init__(self, input_dict):
        properties_file = Path(__file__).parent / 'ObservationProperties.yaml'
        with open(properties_file, 'r') as f:
            properties = yaml.safe_load(f.read())
        super().__init__('Observation', '2.0', properties=properties)
        self.list_element = True
        self.pruning_guide = [(self.get('ExpMeterMode') in ['off', False], ['AutoExpMeter', 'ExpMeterExpTime']),
                              (self.get('ExpMeterMode') != 'control', ['ExpMeterBin', 'ExpMeterThreshold']),
                              (self.get('AutoExpMeter') == True, ['ExpMeterExpTime']),
                              (self.get('AutoNDFilters') == True, ['CalND1', 'CalND2']),
                              (self.get('TakeSimulCal') == False, ['AutoNDFilters', 'CalND1', 'CalND2']),
                              (abs(self.get('NodE')) < 0.01  and abs(self.get('NodN')) < 0.01, ['NodE', 'NodN']),
                              ]
        self.from_dict(input_dict)
        try:
            WAVEBINS = ktl.cache('kpf_expmeter', 'WAVEBINS')
            self.expmeter_bands = [f"{float(b):.0f}nm" for b in WAVEBINS.read().split()]
        except:
            self.expmeter_bands = [f"{float(b):.0f}nm" for b in [498.12, 604.38, 710.62, 816.88]]


    def validate(self):
        '''
        '''
        valid = True
        for p in self.properties:
            if self.get(p['name']) is None:
                print(f"ERROR: {p['name']} is undefined, default is {p['defaultvalue']}")
                valid = False
        # Check if Object is empty
        if self.get('Object') in ['', None]:
            print(f"ERROR: Object field is empty")
            valid = False
        # Check that ExpMeterBin is in [1,2,3,4]
        if self.get('ExpMeterBin') not in [1, 2, 3, 4]:
            print(f"ERROR: ExpMeterBin must be 1, 2, 3, or 4")
            valid = False
        # Check that boolean value properties are reasonable 
        ok_booleans = [True, 'true', 'on', 'On', 1, '1',
                       False, 'false', 'off', 'Off', 0, '0']
        for p in self.properties:
            if p['valuetype'] in [bool, 'bool']:
                if self.get(p['name']) not in ok_booleans:
                    print(f"ERROR: {p['name']} is a boolean with value {self.get(p['name'])}")
                    valid = False
        return valid


    def summary(self):
        '''Provide a short text summary of the Observation.
        '''
        details = []
        if self.get('TakeSimulCal') == True:
            details.append(f'simulcal')
        if self.get('ExpMeterMode') == 'control':
            thresh_str = f'{self.get("ExpMeterThreshold")/1e3:,.0f}k'
            bin_str = self.expmeter_bands[self.get("ExpMeterBin")-1]
            details.append(f'{thresh_str}@{bin_str}')
        if abs(self.get('NodE')) > 0.001 or abs(self.get('NodN')) > 0.001:
            details.append('offset')
        details = f"({';'.join(details)})" if len(details) > 0 else ''
        return f"{self.nExp.value:d}x{self.ExpTime.value:.0f}s{details}"


    def __str__(self):
        '''Provide a very short text summary of the Observation.
        '''
        details = []
        if self.get('ExpMeterMode') == 'control':
            details.append('max')
        if abs(self.get('NodE')) > 0.001 or abs(self.get('NodN')) > 0.001:
            details.append('offset')
        details = f"({';'.join(details)})" if len(details) > 0 else ''
        return f"{self.nExp.value:d}x{self.ExpTime.value:.0f}s{details}"


    def add_comment(self, pname):
        # Object is empty
        if self.get('Object') in ['', None]:
            if pname in ['Object']:
                return ' # Object field is empty'
        # Exposure Meter is off
        if self.get('ExpMeterMode') in ['off', False]:
            if pname in ['AutoExpMeter', 'ExpMeterExpTime', 'ExpMeterThreshold', 'ExpMeterBin']:
                return ' # Unused: ExpMeterMode = off'
        # AutoExpMeter is True
        if self.get('AutoExpMeter') == True:
            if pname == 'ExpMeterExpTime':
                return ' # Unused: AutoExpMeter = True'
        # ExpMeterMode is not Control
        if self.get('ExpMeterMode') != 'control':
            if pname in ['ExpMeterBin', 'ExpMeterThreshold']:
                return ' # Unused: ExpMeterMode != control'
        # AutoNDFilters is True
        if self.get('AutoNDFilters') == True:
            if pname in ['CalND1', 'CalND2']:
                return ' # Unused: AutoNDFilters = True'
        # TakeSimulCal is False
        if self.get('TakeSimulCal') == False:
            if pname in ['AutoNDFilters', 'CalND1', 'CalND2']:
                return ' # Unused: TakeSimulCal = False'
        # GuideHere is False
        if self.get('GuideHere') == False:
            if pname == 'GuideHere':
                return ' # Tip tilt disabled!'
        return ''
