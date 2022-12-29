import os
from time import sleep
from packaging import version
from pathlib import Path
import yaml
import numpy as np

import ktl

from ddoitranslatormodule.KPFTranslatorFunction import KPFTranslatorFunction
from .. import (log, KPFException, FailedPreCondition, FailedPostCondition,
                FailedToReachDestination, check_input)
from . import register_as_script, check_scriptrun, check_script_stop
from ..guider.SetGuiderFPS import SetGuiderFPS
from ..guider.SetGuiderGain import SetGuiderGain
from ..fiu.InitializeTipTilt import InitializeTipTilt
from ..fiu.SetTipTiltGain import SetTipTiltGain
from ..fiu.ConfigureFIU import ConfigureFIU


class ConfigureForAcqOB(KPFTranslatorFunction):
    '''Script which configures the instrument for Acquisition step.
    
    - Sets target parameters
    - Sets guide camera parameters
    - Sets FIU mode
    - Executes Slew Cal????? (Not implemented yet)
    
    Can be called by `ddoi_script_functions.configure_for_science`.
    '''
    @classmethod
    @check_scriptrun
    def pre_condition(cls, OB, logger, cfg):
        check_input(OB, 'Template_Name', allowed_values=['kpf_sci'])
        check_input(OB, 'Template_Version', version_check=True, value_min='0.3')
        return True

    @classmethod
    @register_as_script(Path(__file__).name, os.getpid())
    def perform(cls, OB, logger, cfg):
        log.info('-------------------------')
        log.info(f"Running ConfigureForCalOB")
        for key in OB:
            if key not in ['SEQ_Darks', 'SEQ_Calibrations']:
                log.debug(f"  {key}: {OB[key]}")
            else:
                log.debug(f"  {key}:")
                for entry in OB[key]:
                    log.debug(f"    {entry}")
        log.info('-------------------------')

        # Set Target Paramerts from OB
        log.info(f"Setting target parameters")
#         TargetName
#         GaiaID
#         2MASSID
#         Parallax
#         RadialVelocity
#         Gmag
#         Jmag
#         Teff

        # Set guide camera parameters (only manual supported for now)
        if OB.get('GuideMode', 'manual') != 'manual':
            log.warning('GuideMode = "manual" is the only supported mode')
        InitializeTipTilt.execute({})
        SetGuiderFPS.execute(OB)
        SetGuiderGain.execute(OB)
        SetTipTiltGain.execute(OB)

        # Set FIU Mode
        ConfigureFIU.execute({'mode': 'observing'})

    @classmethod
    def post_condition(cls, OB, logger, cfg):
        return True
