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
        if isinstance(OBinput, ObservingBlock):
            OBdict = OBinput.to_dict()
        elif OBinput in ['', None]:
            OBdict = {}
        elif isinstance(OBinput, str):
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
                raise InvalidObservingBlock(f"OB contains observations without a target")

    def to_dict(self):
        OB = {}
        if self.Target is not None:
            OB['Target'] = self.Target.to_dict()
        if len(self.Observations() > 0:
            OB['Observations'] = [o.to_dict() for o in self.Observations]
        if len(self.Calibrations() > 0:
            OB['Calibrations'] = [c.to_dict() for c in self.Calibrations]
