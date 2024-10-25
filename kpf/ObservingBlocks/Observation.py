from kpf.ObservingBlocks import BaseOBComponent

observation_properties=[('Object', '', str),
                        ('nExp', 1, int),
                        ('ExpTime', 1, float),
                        ('TriggerCaHK', True, bool),
                        ('TriggerGreen', True, bool),
                        ('TriggerRed', True, bool),
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

    def __str__(self):
        return f"{self.nExp.value:d}x{self.ExpTime.value:.0f}s"

    def to_lines(self, comments=False):
        lines = []
        i = 0
        for p in self.properties:
            if self.get(p[0]) is not None:
                i += 1
                if i == 1:
                    lines.append(f"- {p[0]}: {self.get(p[0])}")
                else:
                    lines.append(f"  {p[0]}: {self.get(p[0])}")
        return lines
