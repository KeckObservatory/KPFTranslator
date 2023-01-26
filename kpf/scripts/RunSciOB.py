import time
from pathlib import Path

import ktl

from KPFTranslatorFunction import KPFTranslatorFunction
from .. import (log, KPFException, FailedPreCondition, FailedPostCondition,
                FailedToReachDestination, check_input)
from .ConfigureForAcquisition import ConfigureForAcquisition
from .ConfigureForScience import ConfigureForScience
from ..fiu.StartTipTilt import StartTipTilt
# from ..utils.CorrectDAR import CorrectDAR
from .ExecuteSciSequence import ExecuteSciSequence
from .CleanupAfterScience import CleanupAfterScience


class RunSciOB(KPFTranslatorFunction):
    '''Script to run a full Science OB from the command line.
    
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

        # Configure: 
        log.info(f"Configuring for Acquisition: setting up guider and FIU")
        ConfigureForAcquisition.execute(OB)
        log.info(f"Configuring for Science: setting up spectrograph")
        ConfigureForScience.execute(OB)

        print()
        print("########################################")
        print("Before continuing, please ensure that:")
        print("  1) The OA has placed the star on the KPF PO")
        print("  2) We are not guiding (you can verify on FACSUM)")
        print("  3) The octagon has completed its move")
        print()
        print("If all of those are true, press 'Enter' to continue ...")
        print("########################################")
        print()
        user_input = input()

        log.info(f"Starting tip tilt loops")
        StartTipTilt.execute({})
#         CorrectDAR.execute({})
        log.info(f"Sleeping 3 seconds to allow loops to close")
        time.sleep(3)
        
        # Execute the Science Sequence
        #   Wrap in try/except so that cleanup happens
        try:
            ExecuteSciSequence.execute(OB)
        except Exception as e:
            log.error("ExecuteCalSequence failed:")
            log.error(e)
        # Cleanup: 
        CleanupAfterScience.execute(OB)

    @classmethod
    def post_condition(cls, OB, logger, cfg):
        return True
