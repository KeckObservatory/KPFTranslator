import os
from time import sleep
from pathlib import Path
import numpy as np
import subprocess

import ktl

from ddoitranslatormodule.KPFTranslatorFunction import KPFTranslatorFunction

from ddoi_telescope_translator.pmfm import PMFM


from .. import (KPFException, FailedPreCondition, FailedPostCondition,
                FailedToReachDestination, check_input)
from . import register_script, obey_scriptrun, check_scriptstop, add_script_log
from .ConfigureForAcquisition import ConfigureForAcquisition
from ..guider.TakeGuiderCube import TakeGuiderCube


def comira(command, message):
    pass

notes = '''From kpfMias.sh

# Big picture sequence (skipping details)
miasLock
initOnce = saveOldValues
cleanUp
greeting
initCheck
requestParameters

# Positive PMFM images
getSeriesNumber
setITime
setACSPmfm
takeImage
askUser (whether to continue)
requestParameters
#Optional additional images at +PMFM
takeImage

# Negative PMFM images
setACSPmfm
takeImage (take multiple images)

restoreValues
setACSPmfm 0
analyze
restoreValues
'''


class RunMira(KPFTranslatorFunction):
    '''Replacement for kpfMias.sh
    '''
    @classmethod
    @obey_scriptrun
    def pre_condition(cls, OB, logger, cfg):
        return True

    @classmethod
    @register_script(Path(__file__).name, os.getpid())
    def perform(cls, OB, logger, cfg):
        log.info('-------------------------')
        log.info(f"Running RunMira")
        for key in OB:
            log.debug(f"  {key}: {OB[key]}")
        log.info('-------------------------')

        # Check lockfile, if set, pop up for OA
        # Initcheck: check DCS simulation, set data directory
        # Query Mira parameters from operator via GUI
        
        # Set PMFM
        ConfigureForAcquisition.execute(OB)
        PMFM.execute({'pmfm_nm': OB.get('PMFM')})

        # Take CRED2 trigger file (without full cube)
        TakeGuiderCube.execute({'duration': OB.get('GuiderDuration'),
                                'ImageCube': False})
        lastfile = ktl.cache('kpfguide', 'LASTTRIGFILE')



    @classmethod
    def post_condition(cls, OB, logger, cfg):
        return True
