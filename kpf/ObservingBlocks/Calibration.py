from kpf.ObservingBlocks import BaseOBComponent

calibration_properties=[('CalSource', 'EtalonFiber', str),
                        ('Object', '', str),
                        ('nExp', 1, int),
                        ('ExpTime', 1, float),
                        ('TriggerCaHK', True, bool),
                        ('TriggerGreen', True, bool),
                        ('TriggerRed', True, bool),
                        ('CalND1', 'OD 0.1', str),
                        ('CalND2', 'OD 0.1', str),
                        ('SSS_Science', True, bool),
                        ('SSS_Sky', True, bool),
                        ('TakeSimulCal', False, bool),
                        ('FF_FiberPos', None, str),
                        ('ExpMeterMode', 'off', str),
                        ('ExpMeterExpTime', 1, float),
                        ('ExpMeterBin', 1, int),
                        ('ExpMeterThreshold', None, float),
                         ]

class Calibration(BaseOBComponent):
    def __init__(self, input_dict):
        super().__init__('Calibration', '2.0', properties=calibration_properties)
        self.from_dict(input_dict)
        # Remove Unused Parameters if Dark is True
        self.prune()
    
    def prune(self):
        if self.get('Dark') == True:
            for p in self.properties:
                if p[0] in ['CalSource', 'CalND1', 'CalND2', 'SSS_Science', 'SSS_Sky',
                            'TakeSimulCal', 'FF_FiberPos', 'ExpMeterMode',
                            'ExpMeterExpTime', 'ExpMeterBin', 'ExpMeterThreshold']:
                    self.set(p[0], None)
        return self
