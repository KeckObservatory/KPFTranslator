import time
from pathlib import Path

import ktl

from ddoitranslatormodule.KPFTranslatorFunction import KPFTranslatorFunction
from .. import (log, KPFException, FailedPreCondition, FailedPostCondition,
                FailedToReachDestination, check_input)
from .StartTriggerFile import StartTriggerFile
from .StopTriggerFile import StopTriggerFile
from .WaitForTriggerFile import WaitForTriggerFile


class TakeGuiderCube(KPFTranslatorFunction):
    '''
    
    ARGS: None
    '''
    @classmethod
    def pre_condition(cls, args, logger, cfg):
        check_input(args, 'duration', value_min=0)
        return True

    @classmethod
    def perform(cls, args, logger, cfg):
        duration = float(args.get('duration'))
        kpfguide = ktl.cache('kpfguide')
        trigcube = kpfguide['TRIGCUBE'].read()
        kpfguide['TRIGCUBE'].write('Active')
        initial_lastfile = kpfguide['LASTTRIGFILE'].read()
        all_loops = kpfguide['ALL_LOOPS'].read()
        log.info(f"Starting guider cube data collection, duration = {duration:.1f} s")
        StartTriggerFile.execute({})
        time.sleep(duration)
        StopTriggerFile.execute({})
        kpfguide['ALL_LOOPS'].write('Inactive', wait=False)
        WaitForTriggerFile.execute({'initial_lastfile': initial_lastfile})
        kpfguide['TRIGCUBE'].write(trigcube)
        if all_loops == 'Active':
            kpfguide['ALL_LOOPS'].write('Active')

    @classmethod
    def post_condition(cls, args, logger, cfg):
        return True

    @classmethod
    def add_cmdline_args(cls, parser, cfg=None):
        '''The arguments to add to the command line interface.
        '''
        from collections import OrderedDict
        args_to_add = OrderedDict()
        args_to_add['duration'] = {'type': float,
                                   'help': 'The duration in seconds.'}

        parser = cls._add_args(parser, args_to_add, print_only=False)
        return super().add_cmdline_args(parser, cfg)
