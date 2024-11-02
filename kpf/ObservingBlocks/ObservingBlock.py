from pathlib import Path
import yaml

from kpf.ObservingBlocks.Calibration import Calibration
from kpf.ObservingBlocks.Observation import Observation
from kpf.ObservingBlocks.Target import Target

from kpf import log, KPFException, InvalidObservingBlock


class ObservingBlock(object):
    def __init__(self, OBinput):
        if isinstance(OBinput, dict):
            OBdict = OBinput
        elif isinstance(OBinput, ObservingBlock):
            OBdict = OBinput.to_dict()
        elif OBinput in ['', None]:
            OBdict = {}
        elif isinstance(OBinput, str) or isinstance(OBinput, Path):
            file = Path(OBinput).expanduser().absolute()
            if file.exists() is True:
                try:
                    with open(file, 'r') as f:
                        OBdict = yaml.safe_load(f)
                except Exception as e:
                    log.error(f'Unable to parse input as yaml file')
                    log.error(f'{OBinput}')
                    OBdict = {}
            else:
                log.error(f'Unable to locate file: {OBinput}')
                OBdict = {}
        else:
            log.error(f'Unable to parse input as ObservingBlock')
            log.error(f'{OBinput}')
            OBdict = {}

        # OB Metadata
        self.ProgramID = OBdict.get('ProgramID', '')
        self.AssociatedPrograms = OBdict.get('AssociatedPrograms', '')
        self.CommentToObserver = OBdict.get('CommentToObserver', '')
        # Target
        target = OBdict.get('Target', None)
        if target is None:
            self.Target = None
        else:
            self.Target = Target(target)
        # Observations
        observations = OBdict.get('Observations', [])
        self.Observations = [Observation(obs) for obs in observations]
        # Calibrations
        calibrations = OBdict.get('Calibrations', [])
        self.Calibrations = [Calibration(cal) for cal in calibrations]

    def validate(self):
        # Check that components are the correct types and are individually valid
        if self.Target is not None:
            if not isinstance(self.Target, Target):
                raise InvalidObservingBlock('Target component is not a Target object')
            if not self.Target.validate():
                raise InvalidObservingBlock('Target component is not a valid Target object')
        for i,observation in enumerate(self.Observations):
            if not isinstance(observation, Observation):
                raise InvalidObservingBlock(f'Observation component {i+1} is not a Observation object')
            if not observation.validate():
                raise InvalidObservingBlock('Observation component {i+1} is not a valid Observation object')
        for i,calibration in enumerate(self.Calibrations):
            if not isinstance(calibration, Calibration):
                raise InvalidObservingBlock(f'Calibration component {i+1} is not a Calibration object')
            if not calibration.validate():
                raise InvalidObservingBlock('Calibration component {i+1} is not a valid Calibration object')

        # If we have science observations, we must have a target
        if len(self.Observations) > 0:
            if self.Target is None:
                raise InvalidObservingBlock(f"contains observations without a target")

        # We should have at least one observation or calibration
        if len(self.Observations) == 0 and len(self.Calibrations) == 0:
            raise InvalidObservingBlock(f"contains no observations and no calibrations")

    def to_dict(self):
        OB = {}
        if self.Target is not None:
            OB['Target'] = self.Target.to_dict()
        if len(self.Observations) > 0:
            OB['Observations'] = [o.to_dict() for o in self.Observations]
        if len(self.Calibrations) > 0:
            OB['Calibrations'] = [c.to_dict() for c in self.Calibrations]

    def __str__(self):
        if self.Target is not None:
            out = f"{self.Target}"
        else:
            out = 'unknown        unknown       unknown '
        for obs in self.Observations:
            out += f" {obs}"
        return out

    def __repr__(self):
        lines = []
        if self.Target is not None:
            lines += ['Target:']
            lines += self.Target.to_lines()
        if len(self.Observations) > 0:
            lines += ['Observations:']
            for obs in self.Observations:
                lines += obs.to_lines()
        if len(self.Calibrations) > 0:
            lines += ['Calibrations:']
            for cal in self.Calibrations:
                lines += cal.to_lines()
        return '\n'.join(lines)


def convert_v1_to_v2(OBinput):
    if type(OBinput) in [str, Path]:
        with open(OBinput, 'r') as f:
            OBv1 = yaml.safe_load(f.read())
    t = Target.resolve_target_name(f"Gaia {OB['GaiaID']}")
    t['TargetName'] = OBv1['TargetName']
    OB = ObservingBlock()
    OB.Target = t
    for obs_v1 in OBv1['SEQ_Observations']:
        obs = Observation(obs_v1)
        OB.Observations.append(obs)

    return OB
