from pathlib import Path
import yaml

from kpf.ObservingBlocks import BaseOBComponent


class Calibration(BaseOBComponent):
    def __init__(self, input_dict):
        properties_file = Path(__file__).parent / 'CalibrationProperties.yaml'
        with open(properties_file, 'r') as f:
            properties = yaml.safe_load(f.read())
        super().__init__('Calibration', '2.0', properties=properties)
        self.from_dict(input_dict)
        # Remove Unused Parameters if Dark is True
        self.prune()


    def prune(self):
        if self.get('CalSource').lower() in ['dark', 'home']:
            for pname in ['IntensityMonitor', 'CalND1', 'CalND2',
                          'OpenScienceShutter', 'OpenSkyShutter',
                          'TakeSimulCal', 'WideFlatPos', 'ExpMeterMode',
                          'ExpMeterExpTime', 'ExpMeterBin',
                          'ExpMeterThreshold']:
                self.set(pname, None)

    def to_lines(self, comments=False):
        self.prune()
        lines = []
        i = 0
        for p in self.properties:
            if self.get(p['name']) is not None:
                i += 1
                if i == 1:
                    lines.append(f"- {p['name']}: {self.get(p['name'])}")
                else:
                    lines.append(f"  {p['name']}: {self.get(p['name'])}")
        return lines

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