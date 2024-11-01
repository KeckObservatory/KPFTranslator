from pathlib import Path
import yaml

from kpf.ObservingBlocks import BaseOBComponent


class Observation(BaseOBComponent):
    def __init__(self, input_dict):
        properties_file = Path(__file__).parent / 'ObservationProperties.yaml'
        with open(properties_file, 'r') as f:
            properties = yaml.safe_load(f.read())
        super().__init__('Observation', '2.0', properties=properties)
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
