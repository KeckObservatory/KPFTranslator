import time
import os
from pathlib import Path

import ktl

from kpf.KPFTranslatorFunction import KPFTranslatorFunction
from kpf import (log, KPFException, FailedPreCondition, FailedPostCondition,
                 FailedToReachDestination, check_input)
from kpf.scripts import (set_script_keywords, clear_script_keywords,
                         add_script_log, check_script_running, check_scriptstop)
from kpf.scripts.ConfigureForAcquisition import ConfigureForAcquisition
from kpf.scripts.WaitForConfigureAcquisition import WaitForConfigureAcquisition
from kpf.scripts.ConfigureForScience import ConfigureForScience
from kpf.scripts.CleanupAfterScience import CleanupAfterScience
from kpf.scripts.WaitForConfigureScience import WaitForConfigureScience
from kpf.scripts.ExecuteSci import ExecuteSci
from kpf.fiu.StartTipTilt import StartTipTilt


class RunSciOB(KPFTranslatorFunction):
    '''Script to run a full Science OB from the command line.

    This must have arguments as input, typically from a file using the `-f`
    command line tool.

    Not intended to be called by DDOI's execution engine. This script replaces
    the DDOI Script.

    This script is abortable.  When `.abort_execution()` is invoked, the
    `kpconfig.SCRIPTSTOP` is set to Yes.  This script checked for this value at
    various locations in the script.  As a result, the script will not stop
    immediately, but will stop when it reaches a breakpoint.

    ARGS:
    =====
    None
    '''
    abortable = True

    @classmethod
    def pre_condition(cls, OB, logger, cfg):
        check_input(OB, 'Template_Name', allowed_values=['kpf_sci'])
        check_input(OB, 'Template_Version', version_check=True, value_min='0.5')

    @classmethod
    @add_script_log(Path(__file__).name.replace(".py", ""))
    def perform(cls, OB, logger, cfg):
        log.info('-------------------------')
        log.info(f"Running {cls.__name__}")
        log.info('-------------------------')

        check_scriptstop()

        # Configure: 
        log.info(f"Configuring for Acquisition")
        ConfigureForAcquisition.execute(OB)
        WaitForConfigureAcquisition.execute(OB)

        check_scriptstop()

        log.debug('Asking for user input')
        print()
        print("########################################")
        print("Before continuing, please ensure that:")
        print("  1) The OA has placed the star on the KPF PO")
        print("  2) We are NOT guiding (you can verify on FACSUM)")
        print()
        print("If both of those are true, press 'Enter' to continue ...")
        print("########################################")
        print()
        user_input = input()
        log.debug(f'response: "{user_input}"')

        check_scriptstop()

        log.info(f"Configuring for Science")
        ConfigureForScience.execute(OB)
        WaitForConfigureScience.execute(OB)

        # Execute Sequences
        check_script_running()
        set_script_keywords(Path(__file__).name, os.getpid())
        # Execute the Cal Sequence
        #   Wrap in try/except so that cleanup happens
        observations = OB.get('SEQ_Observations', [])
        for observation in observations:
            observation['Template_Name'] = 'kpf_sci'
            observation['Template_Version'] = OB['Template_Version']
            log.debug(f"Automatically setting TimedShutter_CaHK: {OB['TriggerCaHK']}")
            observation['TimedShutter_CaHK'] = OB['TriggerCaHK']
            observation['TriggerCaHK'] = OB['TriggerCaHK']
            observation['TriggerGreen'] = OB['TriggerGreen']
            observation['TriggerRed'] = OB['TriggerRed']
            observation['TriggerGuide'] = (OB.get('GuideMode', 'off') != 'off')
            observation['Gmag'] = OB['Gmag']
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
        pass
