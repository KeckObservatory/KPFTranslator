import time
from pathlib import Path
import yaml

import ktl

from ddoitranslatormodule.KPFTranslatorFunction import KPFTranslatorFunction
from .. import (log, KPFException, FailedPreCondition, FailedPostCondition,
                FailedToReachDestination, check_input)
from . import (set_script_keywords, clear_script_keywords, add_script_log,
               check_script_running, check_scriptstop)
from .EndOfNight import EndOfNight
from .StartOfNight import StartOfNight
from .RunCalOB import RunCalOB
from .RunSciOB import RunSciOB
from ..utils.SendEmail import SendEmail


##-------------------------------------------------------------------------
## RunTwilightRVStandard
##-------------------------------------------------------------------------
class RunTwilightRVStandard(KPFTranslatorFunction):
    '''
    - Start Twilight script
    - Script: run StartOfNight
    - OA: Select a Mira star near the science target
    - OA: Slew to Mira target
    - OA: Perform Mira
    - OA: Start slew to target star
    - Script: Start Sci OB + Slew Cal
    - Script: Obtain science data
    - OA: Release to regular use, OA can park or do other tasks
    - Script: run EndOfNight
    - Script: run Calibration
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
        print('Running StartOfNight')
#         StartOfNight.execute({})

        # ---------------------------------
        # OA Focus
        # ---------------------------------
        log.debug(f"Pausing to allow OA to slew and focus")
        msg = ["Thank you for executing a KPF Twilight Stability Measurement.",
               "If you encounter urgent problems or questions contact one of",
               "the KPF SAs.  Contact info:",
               "    Josh Walawender: 808-990-4294 (cell)",
               "",
               "Please load the starlist at",
               "/s/starlists/kpftwilight/starlist.txt",
               f"our target will be {targname}.",
               "",
               "Please begin a slew to a Mira star near the target.  When Mira",
               "is complete, press Enter to continue (or 'q' to abort and quit).",
               "",
               ]
        for line in msg:
            print(line)
        user_input = input()
        if user_input.lower() in ['q', 'quit']:
            log.warning('User requested quit. Quitting')
            return

        # ---------------------------------
        # OA Focus and Slew to Target
        # ---------------------------------
        print('Running RunSciOB')
#         RunSciOB.execute({})

        # ---------------------------------
        # Done with telescope
        # ---------------------------------
        log.debug('Observations complete. Alerting OA.')
        print('Observation complete. You may park the telescope or do whatever')
        print('else is needed. Please leave this script running as it will')
        print('perform shutdown and internal calibrations.')
        print()
        print('Running EndOfNight')
#         EndOfNight.execute({})
        print()
        print('Starting internal calibration')
        print('Running RunCalOB')
#         RunCalOB.execute({})
        print()
        print('Internal calibrations complete')
        email = {'To': 'kpf_info@keck.hawaii.edu,ahoward@caltech.edu,sphalverson@gmail.com',
                 'Subject': 'KPF Twilight Program Completed',
                 'Message': ''}
#         SendEmail.execute(email)


    @classmethod
    def post_condition(cls, args, logger, cfg):
        return True
