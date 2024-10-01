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
