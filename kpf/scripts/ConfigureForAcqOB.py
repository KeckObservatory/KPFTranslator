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
from . import register_script, clear_script, check_script_running
from ..guider.SetGuiderFPS import SetGuiderFPS
from ..guider.SetGuiderGain import SetGuiderGain
from ..fiu.InitializeTipTilt import InitializeTipTilt
from ..fiu.SetTipTiltGain import SetTipTiltGain
from ..fiu.ConfigureFIU import ConfigureFIU


class ConfigureForAcqOB(KPFTranslatorFunction):
    '''Script which configures the instrument for Acquisition step.
    
    - Sets target parameters?
    - Sets guide camera parameters
    - Sets FIU mode
    - Executes Slew Cal????? (Not implemented yet)
    
    Can be called by `ddoi_script_functions.configure_for_science`.
    '''
    @classmethod
    def pre_condition(cls, args, logger, cfg):
        check_script_running()
        # Use file input for OB instead of args (temporary)
        check_input(args, 'OBfile')
        OBfile = Path(args.get('OBfile')).expanduser()
        if OBfile.exists() is True:
            OB = yaml.safe_load(open(OBfile, 'r'))
            log.warning(f"Using OB information from file {OBfile}")
        check_input(OB, 'Template_Name', allowed_values=['kpf_sci'])
        check_input(OB, 'Template_Version', version_check=True, value_min='0.3')
        return True

    @classmethod
    def perform(cls, args, logger, cfg):
        # Register this script with kpfconfig
        register_script(Path(__file__).name, os.getpid())
        # Use file input for OB instead of args (temporary)
        OBfile = Path(args.get('OBfile')).expanduser()
        OB = yaml.safe_load(open(OBfile, 'r'))

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
        InitializeTipTilt.execute({})
#         GuideMode
        SetGuiderFPS.execute(OB)
        SetGuiderGain.execute(OB)
        SetTipTiltGain.execute(OB)

        # Set FIU Mode
        ConfigureFIU.execute({'mode': 'observing'})

        # Register end of this script with kpfconfig
        clear_script()

    @classmethod
    def post_condition(cls, args, logger, cfg):
        return True

    @classmethod
    def add_cmdline_args(cls, parser, cfg=None):
        '''The arguments to add to the command line interface.
        '''
        from collections import OrderedDict
        args_to_add = OrderedDict()
        args_to_add['OBfile'] = {'type': str,
                                 'help': ('A YAML fortmatted file with the OB '
                                          'to be executed. Will override OB '
                                          'data delivered as args.')}
        parser = cls._add_args(parser, args_to_add, print_only=False)
        return super().add_cmdline_args(parser, cfg)
