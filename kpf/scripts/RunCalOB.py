from time import sleep
from pathlib import Path
import os

import ktl

from ddoitranslatormodule.KPFTranslatorFunction import KPFTranslatorFunction
from .. import (log, KPFException, FailedPreCondition, FailedPostCondition,
                FailedToReachDestination, check_input)
from . import set_script_keywords, clear_script_keywords, add_script_log
from .ConfigureForCalibrations import ConfigureForCalibrations
from .ExecuteDark import ExecuteDark
from .ExecuteCal import ExecuteCal
from .CleanupAfterCalibrations import CleanupAfterCalibrations

from ..spectrograph.SetSourceSelectShutters import SetSourceSelectShutters
from ..spectrograph.SetTimedShutters import SetTimedShutters
from ..calbench.SetCalSource import SetCalSource
from ..calbench.SetFlatFieldFiberPos import SetFlatFieldFiberPos



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
    @add_script_log(Path(__file__).name.replace(".py", ""))
    def perform(cls, OB, logger, cfg):
        log.info('-------------------------')
        log.info(f"Running {cls.__name__}")
        for key in OB:
            if key not in ['SEQ_Darks', 'SEQ_Calibrations']:
                log.debug(f"  {key}: {OB[key]}")
            else:
                log.debug(f"  {key}:")
                for entry in OB[key]:
                    log.debug(f"    {entry}")
        log.info('-------------------------')

        scriptallow = ktl.cache('kpfconfig', 'SCRIPTALLOW')
        if scriptallow.read() == 'No':
            log.warning(f"SCRIPTALLOW is No, skipping RunCalOB")
            return False

        # Configure: Turn on Lamps
        ConfigureForCalibrations.execute(OB)

        set_script_keywords(Path(__file__).name, os.getpid())
        # Execute the Dark Sequence
        darks = OB.get('SEQ_Darks', [])
        if len(darks) > 0:
            log.info(f"Setting source select shutters")
            SetSourceSelectShutters.execute({}) # No args defaults all to false
            log.info(f"Setting timed shutters")
            SetTimedShutters.execute({}) # No args defaults all to false
            log.info(f"Setting OCTAGON to Home position")
            SetCalSource.execute({'CalSource': 'Home'})
            log.info(f"Setting FlatField Fiber position to 'Blank'")
            SetFlatFieldFiberPos.execute({'FF_FiberPos': 'Blank'})
        for dark in darks:
            # Wrap in try/except so that cleanup happens
            try:
                ExecuteDark.execute(dark)
            except Exception as e:
                log.error("ExecuteDark failed:")
                log.error(e)
        # Execute the Cal Sequence
        #   Wrap in try/except so that cleanup happens
        cals = OB.get('SEQ_Calibrations', [])
        for cal in cals:
            # No need to specify TimedShutter_CaHK in OB/calibration
            cal['TimedShutter_CaHK'] = OB['TriggerCaHK']
            log.debug(f"Automatically setting TimedShutter_CaHK: {cal['TimedShutter_CaHK']}")
            try:
                ExecuteCal.execute(cal)
            except Exception as e:
                log.error("ExecuteCal failed:")
                log.error(e)
        clear_script_keywords()

        # Cleanup: Turn off lamps
        CleanupAfterCalibrations.execute(OB)

    @classmethod
    def post_condition(cls, OB, logger, cfg):
        return True
