import time
from pathlib import Path
import yaml

import ktl

from ddoitranslatormodule.KPFTranslatorFunction import KPFTranslatorFunction
from .. import (log, KPFException, FailedPreCondition, FailedPostCondition,
                FailedToReachDestination, check_input)
from . import (set_script_keywords, clear_script_keywords, add_script_log,
               check_script_running, check_scriptstop)
from .StartOfNight import StartOfNight
from .ConfigureForAcquisition import ConfigureForAcquisition
from .WaitForConfigureAcquisition import WaitForConfigureAcquisition
from .ConfigureForScience import ConfigureForScience
from .WaitForConfigureScience import WaitForConfigureScience
from .ExecuteSci import ExecuteSci
from .CleanupAfterScience import CleanupAfterScience
from .EndOfNight import EndOfNight
from .RunCalOB import RunCalOB
from ..utils.SendEmail import SendEmail


##-------------------------------------------------------------------------
## RunTwilightRVStandard
##-------------------------------------------------------------------------
class RunTwilightRVStandard(KPFTranslatorFunction):
    '''Executes a twilight observation of one a selected RV standard star. This
    script performs all necessary instrument actions from sart up to shut down.

    Sequence of Actions (and who performs them) once this script is invoked:
    - (Script): run StartOfNight
    - (Script): Start Sci OB + Slew Cal
    - (OA): Slew to target
    - (OA): Perform autofoc
    - (Script): Obtain science data
    - (OA): Release to regular use, OA can park or do other tasks
    - (Script): run EndOfNight
    - (Script): run Calibration
    '''
    @classmethod
    def pre_condition(cls, args, logger, cfg):
        return True

    @classmethod
    @add_script_log(Path(__file__).name.replace(".py", ""))
    def perform(cls, args, logger, cfg):
        targname = "HD157347"
        sciOBfile = Path(f'/s/starlists/kpftwilight/{targname}.yaml')
        if sciOBfile.exists() is False:
            log.error(f"Could not load OB file: {sciOBfile}")
            return
        with open(sciOBfile, 'r') as f:
            sciOB = yaml.safe_load(f)

        calOBfile = Path('/s/starlists/kpftwilight/twilight_program_cal.yaml')
        if calOBfile.exists() is False:
            log.error(f"Could not load OB file: {calOBfile}")
            return
        with open(calOBfile, 'r') as f:
            calOB = yaml.safe_load(f)

        # ---------------------------------
        # Start Of Night
        # ---------------------------------
        StartOfNight.execute({})

        log.info(f"Configuring for Acquisition")
        ConfigureForAcquisition.execute(sciOB)

        # ---------------------------------
        # OA Focus
        # ---------------------------------
        msg = ["",
               "Thank you for executing a KPF Twilight Stability Measurement.",
               "If you encounter urgent problems or questions contact one of",
               "the KPF SAs.  Contact info:",
               "    Josh Walawender: 808-990-4294 (cell)",
               "",
               "Please load the starlist at",
               "/s/starlists/kpftwilight/starlist.txt",
               f"our target will be {targname}.",
               "",
               "The instrument is being configured now, please begin slewing",
               "to the target. Once you are on target:",
               " - Focus on target using autfoc",
               " - Then place the target on the KPF PO",
               "When complete, press Enter to continue (or 'q' to abort/quit).",
               "",
               ]
        for line in msg:
            print(line)
        user_input = input()
        if user_input.lower() in ['q', 'quit']:
            log.warning('User requested quit. Quitting')
            return

        # ---------------------------------
        # Execute Observation
        # ---------------------------------
        WaitForConfigureAcquisition.execute(sciOB)
        log.info(f"Configuring for Science")
        ConfigureForScience.execute(OB)
        WaitForConfigureScience.execute(OB)

        # Execute Sequences
        check_script_running()
        set_script_keywords(Path(__file__).name, os.getpid())
        # Execute the Cal Sequence
        #   Wrap in try/except so that cleanup happens
        observations = sciOB.get('SEQ_Observations', [])
        for observation in observations:
            observation['Template_Name'] = 'kpf_sci'
            observation['Template_Version'] = sciOB['Template_Version']
            log.debug(f"Automatically setting TimedShutter_CaHK: {sciOB['TriggerCaHK']}")
            observation['TimedShutter_CaHK'] = sciOB['TriggerCaHK']
            observation['TriggerCaHK'] = sciOB['TriggerCaHK']
            observation['TriggerGreen'] = sciOB['TriggerGreen']
            observation['TriggerRed'] = sciOB['TriggerRed']
            observation['TriggerGuide'] = (sciOB.get('GuideMode', 'off') != 'off')
            try:
                ExecuteSci.execute(observation)
            except Exception as e:
                log.error("ExecuteSci failed:")
                log.error(e)
        clear_script_keywords()

        # Cleanup
        CleanupAfterScience.execute(OB)

        # ---------------------------------
        # Done with telescope
        # ---------------------------------
        log.debug('Observations complete. Alerting OA.')
        print('Observation complete. You may park the telescope or do whatever')
        print('else is needed. Please leave this script running as it will')
        print('perform shutdown and internal calibrations.')
        print()
#         EndOfNight.execute({})
        print()
        print('Starting internal calibration')
        print('Running RunCalOB')
#         RunCalOB.execute(calOB)
        print()
        print('Internal calibrations complete')
        email = {'To': 'jwalawender@keck.hawaii.edu',
#                  'To': 'kpf_info@keck.hawaii.edu,ahoward@caltech.edu,sphalverson@gmail.com',
                 'Subject': 'KPF Twilight Program Completed',
                 'Message': 'A KPF twilight observation has been completed.'}
#         SendEmail.execute(email)


    @classmethod
    def post_condition(cls, args, logger, cfg):
        return True
