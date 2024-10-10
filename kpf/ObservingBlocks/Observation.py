from kpf.ObservingBlocks import BaseOBComponent

observation_properties=[('Object', '', str),
                        ('nExp', 1, int),
                        ('ExpTime', 1, float),
                        ('TriggerCaHK', True, bool),
                        ('TriggerGreen', True, bool),
                        ('TriggerRed', True, bool),
                        ('FastRead', False, bool,)
                        ('BlockSky', False, bool),
                        ('ExpMeterMode', 'monitor', str),
                        ('AutoExpMeter', True, bool),
                        ('ExpMeterExpTime', 1, float),
                        ('ExpMeterBin', 1, int),
                        ('ExpMeterThreshold', None, float),
                        ('TakeSimulCal', False, bool),
                        ('AutoNDFilters', False, bool),
                        ('CalND1', None, str),
                        ('CalND2', None, str),
                        ('NodN', 0, float),
                        ('NodE', 0, float),
                        ('GuideHere', True, bool),
                         ]

class Observation(BaseOBComponent):
    def __init__(self, input_dict):
        super().__init__('Observation', '2.0', properties=observation_properties)
        self.from_dict(input_dict)
