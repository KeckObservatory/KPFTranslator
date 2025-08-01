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
        self.from_dict(input_dict)
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

    def get_pruning_guide(self):
        return [(self.get('ExpMeterMode') in ['off', False], ['AutoExpMeter', 'ExpMeterExpTime']),
                (self.get('ExpMeterMode') != 'control', ['ExpMeterBin', 'ExpMeterThreshold']),
                (self.get('AutoExpMeter') == True, ['ExpMeterExpTime']),
                (self.get('AutoNDFilters') == True, ['CalND1', 'CalND2']),
                (self.get('TakeSimulCal') == False, ['AutoNDFilters', 'CalND1', 'CalND2']),
#                 (abs(self.get('NodE')) < 0.01  and abs(self.get('NodN')) < 0.01, ['NodE', 'NodN']),
                ]

    def check_property(self, pname):
        if pname == 'Object':
            if self.get(pname) in ['', None]:
                return False, ' # Object field is empty'
        elif pname == 'nExp':
            if self.get(pname) < 1:
                return True, ' # ERROR: nExp < 1'
        elif pname == 'ExpTime':
            if self.get(pname) < 0:
                return True, ' # ERROR: ExpTime < 0'
        elif pname == 'ExpMeterMode':
            if self.get(pname) not in ['off', False, 'control', 'monitor']:
                return True, ' # ERROR: ExpMeterMode invalid'
        elif pname == 'AutoExpMeter':
            if type(self.get(pname)) != bool:
                return True, ' # ERROR: Invalid boolean'
            elif self.get('ExpMeterMode') in ['off', False]:
                return False, ' # Unused: ExpMeterMode = off'
        elif pname == 'ExpMeterExpTime':
            if self.get(pname) < 0:
                return True, ' # ERROR: ExpMeterExpTime < 0'
            elif self.get('ExpMeterMode') in ['off', False]:
                return False, ' # Unused: ExpMeterMode = off'
            elif self.get('AutoExpMeter') == True:
                return False, ' # Unused: AutoExpMeter = True'
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
            elif self.get('TakeSimulCal') == False:
                return False, ' # Unused: TakeSimulCal = False'
            elif self.get('TakeSimulCal') == True and self.get('AutoNDFilters') == True:
                return False, ' # Unused: AutoNDFilters = True'
        elif pname == 'AutoNDFilters':
            if type(self.get(pname)) != bool:
                return True, ' # ERROR: Invalid boolean'
            if self.get('TakeSimulCal') == False:
                return False, ' # Unused: TakeSimulCal = False'
        elif pname == 'GuideHere':
            if type(self.get(pname)) != bool:
                return True, ' # ERROR: Invalid boolean'
            if self.get(pname) == False:
                return False, ' # Tip tilt disabled!'
        elif pname in ['TriggerCaHK', 'TriggerGreen', 'TriggerRed', 'BlockSky', 'TakeSimulCal']:
            print(f"Checking {pname}: {type(self.get(pname))} {self.get(pname)}")
            if type(self.get(pname)) != bool:
                return True, ' # ERROR: Invalid boolean'
        return False, ''


    def validate(self):
        '''
        '''
        valid = True
        for p in self.properties:
            error, comment = self.check_property(p['name'])
            if error == True:
                valid = False
        return valid


    def add_comment(self, pname):
        error, comment = self.check_property(pname)
        return comment


    def summary(self):
        '''Provide a short text summary of the Observation.
        '''
        details = []
        if self.get('TakeSimulCal') == True:
            details.append(f'simulcal')
        if self.get('ExpMeterMode') == 'control':
            thresh_str = f'{self.get("ExpMeterThreshold"):.1f}'
            bin_str = self.expmeter_bands[self.get("ExpMeterBin")-1]
            details.append(f'{thresh_str}@{bin_str}')
#         if abs(self.get('NodE')) > 0.001 or abs(self.get('NodN')) > 0.001:
#             details.append('offset')
        details = f"({';'.join(details)})" if len(details) > 0 else ''
        return f"{self.nExp.value:d}x{self.ExpTime.value:.0f}s{details}"


    def __str__(self):
        '''Provide a very short text summary of the Observation.
        '''
        details = []
        if self.get('ExpMeterMode') == 'control':
            details.append('max')
#         if abs(self.get('NodE')) > 0.001 or abs(self.get('NodN')) > 0.001:
#             details.append('offset')
        details = f"({';'.join(details)})" if len(details) > 0 else ''
        return f"{self.nExp.value:d}x{self.ExpTime.value:.0f}s{details}"
