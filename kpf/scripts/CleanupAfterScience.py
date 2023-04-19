from pathlib import Path

from kpf.KPFTranslatorFunction import KPFTranslatorFunction
from kpf import (log, KPFException, FailedPreCondition, FailedPostCondition,
                 FailedToReachDestination, check_input)
from kpf.scripts import (register_script, obey_scriptrun, check_scriptstop,
                         add_script_log)
from kpf.fiu.StopTipTilt import StopTipTilt
from kpf.spectrograph.StopAgitator import StopAgitator


class CleanupAfterScience(KPFTranslatorFunction):
    '''Script which cleans up at the end of Science OBs.

    Can be called by `ddoi_script_functions.post_observation_cleanup`.

    ARGS:
    =====
    None
    '''
    @classmethod
    @obey_scriptrun
    def pre_condition(cls, OB, logger, cfg):
        return True

    @classmethod
    def perform(cls, OB, logger, cfg):
        log.info('-------------------------')
        log.info(f"Running {cls.__name__}")
        log.info('-------------------------')

        # Turn off tip tilt
        StopTipTilt.execute({})
        StopAgitator.execute({})

    @classmethod
    def post_condition(cls, OB, logger, cfg):
        return True
