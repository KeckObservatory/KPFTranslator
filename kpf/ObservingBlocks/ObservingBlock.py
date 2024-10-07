from kpf.ObservingBlocks.Calibration import Calibration
from kpf.ObservingBlocks.Observation import Observation
from kpf.ObservingBlocks.Target import Target


class ObservingBlock(object):
    def __init__(self):
        self.Target = None
        self.Observations = []
        self.Calibrations = []
        self.Scheduling = None
        self.Metadata = None

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
        if self.Scheduling is not None:
            OB['Scheduling'] = self.Scheduling.to_dict()
        if self.Metadata is not None:
            OB['Metadata'] = self.Metadata.to_dict()
