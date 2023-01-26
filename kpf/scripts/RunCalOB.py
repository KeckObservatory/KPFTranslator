from time import sleep
from pathlib import Path

import ktl

from kpf.KPFTranslatorFunction import KPFTranslatorFunction
from .. import (log, KPFException, FailedPreCondition, FailedPostCondition,
                FailedToReachDestination, check_input)
from .ConfigureForCalibrations import ConfigureForCalibrations
from .ExecuteCalSequence import ExecuteCalSequence
from .CleanupAfterCalibrations import CleanupAfterCalibrations


class RunCalOB(KPFTranslatorFunction):
    '''Script to run a full Calibration OB from the command line.
    
    Not intended to be called by DDOI's execution engine. This script replaces
    the DDOI Script.
    
    This script is abortable.  When the `.abort_execution()` is invoked, the
    `kpconfig.SCRIPTSTOP` is set to Yes.  This script checked for this value at
    various locations in the script.  As a result, the script will not stop
    immediately, but will stop when it reaches a breakpoint.
    '''
    @classmethod
    def pre_condition(cls, OB, logger, cfg):
        return True

    @classmethod
    def perform(cls, OB, logger, cfg):
        log.info('-------------------------')
        log.info(f"Running {cls.__name__}")
        log.info('-------------------------')

        scriptallow = ktl.cache('kpfconfig', 'SCRIPTALLOW')
        if scriptallow.read() == 'No':
            log.warning(f"SCRIPTALLOW is No, skipping RunCalOB")
            return False

        # Configure: Turn on Lamps
        ConfigureForCalibrations.execute(OB)
        # Execute the Cal Sequence
        #   Wrap in try/except so that cleanup happens
        try:
            ExecuteCalSequence.execute(OB)
        except Exception as e:
            log.error("ExecuteCalSequence failed:")
            log.error(e)
        # Cleanup: Turn off lamps
        CleanupAfterCalibrations.execute(OB)

    @classmethod
    def post_condition(cls, OB, logger, cfg):
        return True
