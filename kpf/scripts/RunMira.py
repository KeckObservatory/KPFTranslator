import os
from time import sleep
from pathlib import Path
import numpy as np
import subprocess

import ktl

from kpf.KPFTranslatorFunction import KPFTranslatorFunction

from ddoi_telescope_translator.pmfm import PMFM

from kpf import (log, KPFException, FailedPreCondition, FailedPostCondition,
                 FailedToReachDestination, check_input)
from kpf.scripts import (register_script, obey_scriptrun, check_scriptstop,
                         add_script_log)
from kpf.scripts.ConfigureForAcquisition import ConfigureForAcquisition
from kpf.guider.TakeGuiderCube import TakeGuiderCube


def comira(command, message):
    pass

notes = '''
Thoughts:
* During acquisition have TIPTILT_CALC on to see flux, can we automatically
adjust guide camera settings (gain & FPS) to ensure good measurement?  This
would allow OAs a lot of freedom to choose a Mira star and would be able to use
first science target on many nights.
* No need to preserve KPF camera settings, will be configured by OB or by the
GUI for next target.

Outline:
- miasLock (generate symbolic link)
- greeting (just some simple message echos)
- initCheck (check for DCS simulate mode and debug mode)
- requestParameters <-- replace with automation
- Positive PMFM image
    - getSeriesNumber
    - removeAll
    - set PMFM (include sleep and check)
    - collect image
- Confirm continue?
- Negative PMFM image
    - getSeriesNumber
    - removeAll
    - set PMFM (include sleep and check)
    - collect image
- set PMFM to 0 (do not sleep or wait)
- run analysis
- check for PMFM=0
- cleanup lock file
'''


class RunMira(KPFTranslatorFunction):
    '''Replacement for kpfMias.sh
    '''
    @classmethod
    @obey_scriptrun
    def pre_condition(cls, OB, logger, cfg):
        pass

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
        pass
