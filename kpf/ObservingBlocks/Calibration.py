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
