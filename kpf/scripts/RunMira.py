import os
from time import sleep
from pathlib import Path
import numpy as np
import subprocess

import ktl

from ddoitranslatormodule.KPFTranslatorFunction import KPFTranslatorFunction
from .. import (log, KPFException, FailedPreCondition, FailedPostCondition,
                FailedToReachDestination, check_input)
from . import register_script, obey_scriptrun, check_scriptstop

def comira(command, message):
    pass



def check_mias_lock(SERIESFILE, LOCKFILE):
    if SERIESFILE.exists() and LOCKFILE.exists():
        subprocess.call(['beep'])
        cmd = '''echo 'yesNoMessage Title (title, "Warning !!!");  \
SetWindowPos (600, 300); \
Panel (p1, 0, 0) { \
SetFont ("Dialog", 35); \
SetFGColor (255, 0, 0); \
StaticText ("Warning !!!", 0, 0); } \
Panel (p1, 0, 1, 1, 1, BOTH, NORTHWEST, 1, 1, 10, 10, 10, 10) { \
SetBGColor (255, 0, 0); \
SetFGColor (255, 255, 255); \
SetFont ("Dialog", 25); \
StaticText ("Application is locked!", 0, 1); \
StaticText ("Another script may be running! ", 0, 2); \
StaticText ("To continue anyways, press Yes", 0, 3); \
StaticText ("To abort, press No", 0, 4); } \
' | $COMIRA $MIRAHOST $MIRAPORT'''



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

        SERIESNR = 0
        SERIESFILE = Path("/s/nightly1/log/MiasNumber")
        LOCKFILE = Path("/s/nightly1/log/mias/kpfMias.locked")
        
        


    @classmethod
    def post_condition(cls, OB, logger, cfg):
        return True
