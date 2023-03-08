import time
from pathlib import Path

import ktl

from ddoitranslatormodule.KPFTranslatorFunction import KPFTranslatorFunction
from .. import (log, KPFException, FailedPreCondition, FailedPostCondition,
                FailedToReachDestination, check_input)
from .SendEmail import SendEmail
from ..script.RunCalOB import RunCalOB
from ..script.RunSciOB import RunSciOB


##-------------------------------------------------------------------------
## ExecuteTwilightRVStandard
##-------------------------------------------------------------------------
class ExecuteTwilightRVStandard(KPFTranslatorFunction):
    '''
    
    - Start Twilight script
    - Select a Mira star near the science target
    - Slew to Mira target
    - Perform Mira
    - Start slew to target star
    - Start Sci OB + Slew Cal
    - Obtain science data
    - Return telescope to regular use
    - Calibration
    
    '''
    @classmethod
    def pre_condition(cls, args, logger, cfg):
        return True

    @classmethod
    def perform(cls, args, logger, cfg):
        targname = "HD157347"
        sciOBfile = Path('/s/starlists/teamkeck/{targname}.yaml')
        calOBfile = Path('/s/starlists/teamkeck/twilight_program_cal.yaml')

        # Start Calibrations
        msg = [
               "Please load the starlist at",
               "/s/starlists/teamkeck/starlist_kpfTwilight.txt",
               f"our target will be {targname}.",
               "",
               "Please begin a slew to a Mira star near the target.  When Mira",
               "is complete, press 'q' to quit or any other key to continue.",
               "",
               ]
        for line in msg:
            print(line)
        user_input = input()
        if user_input.lower() in ['q', 'quit']:
            print('Quitting')
            return



    @classmethod
    def post_condition(cls, args, logger, cfg):
        return True
