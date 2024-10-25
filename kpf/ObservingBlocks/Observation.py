from kpf.ObservingBlocks import BaseOBComponent

observation_properties = [{'name': 'Object', 'value': '', 'valuetype': str,
                           'comment': 'Object Name'},
                          {'name': 'nExp', 'value': 1, 'valuetype': int,
                           'comment': 'Number of Exposures'},
                          {'name': 'ExpTime', 'value': 1, 'valuetype': float,
                           'comment': '[seconds] Exposure Time',
                           'precision': 0},
                          {'name': 'TriggerCaHK', 'value': True, 'valuetype': bool,
                           'comment': ''},
                          {'name': 'TriggerGreen', 'value': True, 'valuetype': bool,
                           'comment': ''},
                          {'name': 'TriggerRed', 'value': True, 'valuetype': bool,
                           'comment': ''},
                          {'name': 'BlockSky', 'value': False, 'valuetype': bool,
                           'comment': 'Block the sky fiber during the observation?'},
                          {'name': 'ExpMeterMode', 'value': 'monitor', 'valuetype': str,
                           'comment': 'Exposure meter mode? (monitor, control, off)'},
                          {'name': 'AutoExpMeter', 'value': True, 'valuetype': bool,
                           'comment': ''},
                          {'name': 'ExpMeterExpTime', 'value': 1, 'valuetype': float,
                           'comment': '[seconds] Exposure Time for the exposure meter',
                           'precision': 1},
                          {'name': 'ExpMeterBin', 'value': 1, 'valuetype': int,
                           'comment': ''},
                          {'name': 'ExpMeterThreshold', 'value': 50000, 'valuetype': float,
                           'comment': '',
                           'precision': 0},
                          {'name': 'TakeSimulCal', 'value': True, 'valuetype': bool,
                           'comment': ''},
                          {'name': 'AutoNDFilters', 'value': True, 'valuetype': bool,
                           'comment': ''},
                          {'name': 'CalND1', 'value': 'OD 0.1', 'valuetype': str,
                           'comment': ''},
                          {'name': 'CalND2', 'value': 'OD 0.1', 'valuetype': str,
                           'comment': ''},
                          {'name': 'NodN', 'value': 0, 'valuetype': float,
                           'comment': '',
                           'precision': 2},
                          {'name': 'NodE', 'value': 0, 'valuetype': float,
                           'comment': '',
                           'precision': 2},
                          {'name': 'GuideHere', 'value': True, 'valuetype': bool,
                           'comment': ''},
                         ]

# observation_properties=[('Object', '', str),
#                         ('nExp', 1, int),
#                         ('ExpTime', 1, float),
#                         ('TriggerCaHK', True, bool),
#                         ('TriggerGreen', True, bool),
#                         ('TriggerRed', True, bool),
#                         ('BlockSky', False, bool),
#                         ('ExpMeterMode', 'monitor', str),
#                         ('AutoExpMeter', True, bool),
#                         ('ExpMeterExpTime', 1, float),
#                         ('ExpMeterBin', 1, int),
#                         ('ExpMeterThreshold', None, float),
#                         ('TakeSimulCal', False, bool),
#                         ('AutoNDFilters', False, bool),
#                         ('CalND1', None, str),
#                         ('CalND2', None, str),
#                         ('NodN', 0, float),
#                         ('NodE', 0, float),
#                         ('GuideHere', True, bool),
#                          ]

class Observation(BaseOBComponent):
    def __init__(self, input_dict):
        super().__init__('Observation', '2.0', properties=observation_properties)
        self.from_dict(input_dict)

    def __str__(self):
        return f"{self.nExp.value:d}x{self.ExpTime.value:.0f}s"

    def to_lines(self, comments=False):
        lines = []
        i = 0
        for pdict in self.properties:
            if self.get(pdict['name']) is not None:
                p = getattr(self, pdict['name'])
                i += 1
                if i == 1:
                    lines.append(f"- {pdict['name']}: {str(p)}")
                else:
                    lines.append(f"  {pdict['name']}: {str(p)}")


        return lines
