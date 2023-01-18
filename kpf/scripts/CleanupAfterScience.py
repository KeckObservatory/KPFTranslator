import os
from time import sleep
from packaging import version
from pathlib import Path
import numpy as np

import ktl

from ddoitranslatormodule.KPFTranslatorFunction import KPFTranslatorFunction
from .. import (log, KPFException, FailedPreCondition, FailedPostCondition,
                FailedToReachDestination, check_input)
from . import register_script, obey_scriptrun, check_scriptstop
from ..fiu.StopTipTilt import StopTipTilt


class CleanupAfterScience(KPFTranslatorFunction):
    '''Script which cleans up at the end of Science OBs.
    
    Can be called by `ddoi_script_functions.post_observation_cleanup`.
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

    @classmethod
    def post_condition(cls, OB, logger, cfg):
        return True
