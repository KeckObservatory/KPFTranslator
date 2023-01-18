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
from . import register_script, obey_scriptrun, check_scriptstop
from ..guider.SetGuiderFPS import SetGuiderFPS
from ..guider.SetGuiderGain import SetGuiderGain
from ..fiu.InitializeTipTilt import InitializeTipTilt
from ..fiu.SetTipTiltGain import SetTipTiltGain
from ..fiu.ConfigureFIU import ConfigureFIU


class ConfigureForAcquisition(KPFTranslatorFunction):
    '''Script which configures the instrument for Acquisition step.
    
    - Sets target parameters
    - Sets guide camera parameters
    - Sets FIU mode
    - Executes Slew Cal????? (Not implemented yet)
    
    Can be called by `ddoi_script_functions.configure_for_science`.
    '''
    @classmethod
    @obey_scriptrun
    def pre_condition(cls, OB, logger, cfg):
        check_input(OB, 'Template_Name', allowed_values=['kpf_sci'])
        check_input(OB, 'Template_Version', version_check=True, value_min='0.5')
#         check_input(OB, 'TargetName')
#         check_input(OB, 'GaiaID')
#         check_input(OB, '2MASSID')
#         check_input(OB, 'Parallax')
#         check_input(OB, 'RadialVelocity')
#         check_input(OB, 'Gmag')
#         check_input(OB, 'Jmag')
#         check_input(OB, 'Teff')
        return True

    @classmethod
    def perform(cls, OB, logger, cfg):
        log.info('-------------------------')
        log.info(f"Running {cls.__name__}")
        for key in OB:
            if key not in ['SEQ_Observations']:
                log.debug(f"  {key}: {OB[key]}")
            else:
                log.debug(f"  {key}:")
                for entry in OB[key]:
                    log.debug(f"    {entry}")
        log.info('-------------------------')

        dcs = ktl.cache('dcs')
        kpfconfig = ktl.cache('kpfconfig')
        kpf_expmeter = ktl.cache('kpf_expmeter')

        ## Execute Slew Cal if Requested
        if kpfconfig['SLEWCALREQ'].read(binary=True) is True:
            slewcal_argsfile = Path(kpfconfig['SLEWCALFILE'].read())
            log.info(f"Beginning Slew Cal")
            log.debug(f"Using: {slewcal_argsfile}")
            with open(slewcal_argsfile, 'r') as file
                slewcal_args = yaml.safe_load(file)
            slewcal_args['TriggerCaHK'] = OB['TriggerCaHK']
            slewcal_args['TriggerGreen'] = OB['TriggerGreen']
            slewcal_args['TriggerRed'] = OB['TriggerRed']
            ExecuteSlewCals.execute(slewcal_args)

        # Set FIU Mode
        log.info('Setting FIU mode to Observing')
        ConfigureFIU.execute({'mode': 'Observing', 'wait': False})

        # Set Target Parameters from OB
        log.info(f"Setting target parameters")
        kpfconfig['TARGET_NAME'].write(OB.get('TargetName', ''))
        kpfconfig['TARGET_GAIA'].write(OB.get('GaiaID', ''))
        kpfconfig['TARGET_2MASS'].write(OB.get('2MASSID', ''))
        kpfconfig['TARGET_GMAG'].write(OB.get('Gmag', ''))
        kpfconfig['TARGET_JMAG'].write(OB.get('Jmag', ''))
        kpf_expmeter['TARGET_TEFF'].write(OB.get('Teff', 0))
        dcs['TARGPLAX'].write(OB.get('Parallax', 0))
        dcs['TARGRADV'].write(OB.get('RadialVelocity', 0))

        # Set guide camera parameters (only manual supported for now)
        if OB.get('GuideMode', 'manual') != 'manual':
            log.warning('GuideMode = "manual" is the only supported mode')
        if OB.get('GuideCamGain', None) is not None:
            SetGuiderGain.execute(OB)
        if OB.get('GuideFPS', None) is not None:
            SetGuiderFPS.execute(OB)
        if OB.get('GuideLoopGain', None) is not None:
            SetTipTiltGain.execute(OB)

    @classmethod
    def post_condition(cls, OB, logger, cfg):
        return True
