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

    def prune(self):
        if self.get('ExpMeterMode') in ['monitor', 'off']:
            for pname in ['ExpMeterBin', 'ExpMeterThreshold']:
                self.set(pname, None)
        if self.get('AutoExpMeter') is True:
            for pname in ['ExpMeterExpTime']:
                self.set(pname, None)
        if self.get('ExpMeterMode') in ['off']:
            for pname in ['AutoExpMeter', 'ExpMeterExpTime']:
                self.set(pname, None)
        if self.get('AutoNDFilters') is True:
            for pname in ['CalND1', 'CalND2']:
                self.set(pname, None)
        if self.get('TakeSimulCal') is False:
            for pname in ['AutoNDFilters']:
                self.set(pname, None)
        if self.get('NodE') is None and self.get('NodN') is None:
            for pname in ['NodE', 'NodN']:
                self.set(pname, None)


    def summary(self):
        details = []
        if self.get('TakeSimulCal') == True:
            details.append(f'simulcal')
        if self.get('ExpMeterMode') == 'control':
            details.append(f'EM={self.get("ExpMeterBin")}:{self.get("ExpMeterThreshold"):.0f}')
        if abs(self.get('NodE')) > 0.001 or abs(self.get('NodN')) > 0.001:
            details.append('offset')
        details = f"({','.join(details)})" if len(details) > 0 else ''
        return f"{self.nExp.value:d}x{self.ExpTime.value:.0f}s{details}"


    def __str__(self):
        details = []
        if self.get('ExpMeterMode') == 'control':
            details.append('max')
        if abs(self.get('NodE')) > 0.001 or abs(self.get('NodN')) > 0.001:
            details.append('offset')
        details = f"({','.join(details)})" if len(details) > 0 else ''
        return f"{self.nExp.value:d}x{self.ExpTime.value:.0f}s{details}"


    def to_lines(self, comments=False):
        self.prune()
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
