import time
from pathlib import Path

import ktl

from ddoitranslatormodule.KPFTranslatorFunction import KPFTranslatorFunction
from .. import (log, KPFException, FailedPreCondition, FailedPostCondition,
                FailedToReachDestination, check_input)
from . import set_script_keywords, clear_script_keywords, add_script_log
from .ConfigureForAcquisition import ConfigureForAcquisition
from .ConfigureForScience import ConfigureForScience
from ..fiu.StartTipTilt import StartTipTilt

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
    abortable = True

    @classmethod
    def abort_execution(args, logger, cfg):
        scriptstop = ktl.cache('kpfconfig', 'SCRIPTSTOP')
        log.warning('Abort recieved, setting kpfconfig.SCRTIPSTOP=Yes')
        scriptstop.write('Yes')

    @classmethod
    def pre_condition(cls, OB, logger, cfg):
        check_input(OB, 'Template_Name', allowed_values=['kpf_sci'])
        check_input(OB, 'Template_Version', version_check=True, value_min='0.5')
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
        log.info(f"Sleeping 3 seconds to allow loops to close")
        time.sleep(3)

        # Execute Sequences
        set_script_keywords(Path(__file__).name, os.getpid())
        # Execute the Cal Sequence
        #   Wrap in try/except so that cleanup happens
        observations = OB.get('SEQ_Observations', [])
        for observation in observations:
            observation['Template_Name'] = 'kpf_sci'
            observation['Template_Version'] = OB['Template_Version']
            log.debug(f"Automatically setting TimedShutter_CaHK: {OB['TriggerCaHK']}")
            observation['TimedShutter_CaHK'] = OB['TriggerCaHK']
            try:
                ExecuteSci.execute(observation)
            except Exception as e:
                log.error("ExecuteSci failed:")
                log.error(e)
        clear_script_keywords()

        # Cleanup: 
        CleanupAfterScience.execute(OB)

    @classmethod
    def post_condition(cls, OB, logger, cfg):
        return True
