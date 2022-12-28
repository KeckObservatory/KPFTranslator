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
from ..calbench.CalLampPower import CalLampPower
from ..calbench.SetCalSource import SetCalSource
from ..fiu.ConfigureFIU import ConfigureFIU


class ConfigureForSciOB(KPFTranslatorFunction):
    '''Script which configures the instrument for Science observations.
    
    - Turns on lamp power for all sequences
    - Sets octagon / simulcal source & ND filters for first sequence (skip if
      slew cal is selected?)
    - Sets source select shutters
    - Sets triggered detectors

    Can be called by `ddoi_script_functions.configure_for_science`.
    '''
    @classmethod
    @check_scriptrun
    def pre_condition(cls, args, logger, cfg):
        check_script_running()
        # Use file input for OB instead of args (temporary)
        check_input(args, 'OBfile')
        OBfile = Path(args.get('OBfile')).expanduser()
        if OBfile.exists() is True:
            OB = yaml.safe_load(open(OBfile, 'r'))
            log.warning(f"Using OB information from file {OBfile}")
        check_input(OB, 'Template_Name', allowed_values=['kpf_cal'])
        check_input(OB, 'Template_Version', version_check=True, value_min='0.3')
        return True

    @classmethod
    @register_as_script(Path(__file__).name, os.getpid())
    def perform(cls, args, logger, cfg):
        # Register this script with kpfconfig
        register_script(Path(__file__).name, os.getpid())
        # Use file input for OB instead of args (temporary)
        OBfile = Path(args.get('OBfile')).expanduser()
        OB = yaml.safe_load(open(OBfile, 'r'))

        log.info('-------------------------')
        log.info(f"Running ConfigureForSciOB")
        for key in OB:
            if key not in ['SEQ_Observations']:
                log.debug(f"  {key}: {OB[key]}")
            else:
                log.debug(f"  {key}:")
                for entry in OB[key]:
                    log.debug(f"    {entry}")
        log.info('-------------------------')

        # Turn on lamps
        lamps = [seq['CalSource'] for seq in OB.get('SEQ_Observations')\
                 if 'CalSource' in seq.keys()]
        for lamp in set(lamps):
            if lamp in ['Th_daily', 'Th_gold', 'U_daily', 'U_gold',
                        'BrdbandFiber', 'WideFlat']:
                log.debug(f"Ensuring lamp {lamp} is on")
                CalLampPower.execute({'lamp': lamp, 'power': 'on'})

        # Set Octagon
        log.info(f"Set CalSource/Octagon: {lamps[0]}")
        SetCalSource.execute({'CalSource': lamps[0], 'wait': False})

        # Set source select shutters
        log.info(f"Set Source Select Shutters")
        SetSourceSelectShutters.execute({'SciSelect': True, 'SkySelect': True,
                                         'SoCalSci': False, 'SoCalCal': False,
                                         'Cal_SciSky': False})

        # Set triggered detectors
        log.info(f"Set Detector List")
        SetTriggeredDetectors.execute(OB)

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
