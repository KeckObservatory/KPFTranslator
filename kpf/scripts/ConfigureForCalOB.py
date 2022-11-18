from time import sleep
from packaging import version
from pathlib import Path
import yaml
import numpy as np

import ktl

from ddoitranslatormodule.KPFTranslatorFunction import KPFTranslatorFunction
from .. import (log, KPFException, FailedPreCondition, FailedPostCondition,
                FailedToReachDestination, check_input)
from ..calbench.CalLampPower import CalLampPower


class ConfigureForCalOB(KPFTranslatorFunction):
    '''Script which configures the instrument for Cal OBs.
    
    Can be called by `ddoi_script_functions.configure_for_science`.
    '''
    @classmethod
    def pre_condition(cls, args, logger, cfg):
        # Use file input for OB instead of args (temporary)
        check_input(args, 'OBfile')
        OBfile = Path(args.get('OBfile')).expanduser()
        if OBfile.exists() is True:
            OB = yaml.safe_load(open(OBfile, 'r'))
            log.warning(f"Using OB information from file {OBfile}")
        check_input(OB, 'Template_Name', allowed_values=['kpf_cal'])
        check_input(OB, 'Template_Version', allowed_values=['0.3'])
        return True

    @classmethod
    def perform(cls, args, logger, cfg):
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

        # Power up needed lamps
        sequence = OB.get('SEQ_Calibrations')
        lamps = set([x['CalSource'] for x in sequence if x['CalSource'] != 'Home'])
        for lamp in lamps:
            if lamp in ['Th_daily', 'Th_gold', 'U_daily', 'U_gold',
                        'BrdbandFiber', 'WideFlat']:
                CalLampPower.execute({'lamp': lamp, 'power': 'on'})

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
