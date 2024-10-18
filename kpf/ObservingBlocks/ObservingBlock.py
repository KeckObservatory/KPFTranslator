from pathlib import Path
import yaml
from kpf.ObservingBlocks.Calibration import Calibration
from kpf.ObservingBlocks.Observation import Observation
from kpf.ObservingBlocks.Target import Target

from kpf import log, KPFException


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
            assert isinstance(self.Target, Target)
            assert self.Target.validate()
        for observation in self.Observations:
            assert isinstance(observation, Observation)
            assert observation.validate()
        for calibration in self.Calibrations:
            assert isinstance(calibration, Calibration)
            assert calibration.validate()

        # If we have science observations, we must have a target
        if len(self.Observations) > 0:
            assert self.Target is not None

    def to_dict(self):
        OB = {}
        if self.Target is not None:
            OB['Target'] = self.Target.to_dict()
        if len(self.Observations() > 0:
            OB['Observations'] = [o.to_dict() for o in self.Observations]
        if len(self.Calibrations() > 0:
            OB['Calibrations'] = [c.to_dict() for c in self.Calibrations]
