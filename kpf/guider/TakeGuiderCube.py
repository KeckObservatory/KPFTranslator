import time
from pathlib import Path

import ktl

from kpf.KPFTranslatorFunction import KPFTranslatorFunction
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
        # Read initial conditions, so we can set them back at the end
        initial_trigcube = kpfguide['TRIGCUBE'].read()
        initial_lastfile = kpfguide['LASTTRIGFILE'].read()
        initial_all_loops = kpfguide['ALL_LOOPS'].read()

        # Do we want to take the image cube?
        collect_image_cube = args.get('ImageCube', False)
        set_trigcube = {True: 'Active', False: 'Inactive'}[collect_image_cube]
        kpfguide['TRIGCUBE'].write(set_trigcube)

        # Trigger data collection
        log.info(f"Starting guider cube data collection, duration = {duration:.1f} s")
        StartTriggerFile.execute({})
        time.sleep(duration)
        StopTriggerFile.execute({})
        # Stop all loops if we're writing out a full image cube
        if initial_all_loops == 'Active' and collect_image_cube == True:
            kpfguide['ALL_LOOPS'].write('Inactive', wait=False)
        WaitForTriggerFile.execute({'initial_lastfile': initial_lastfile})

        # Reset TRIGCUBE and ALL_LOOPS to initial values
        kpfguide['TRIGCUBE'].write(initial_trigcube)
        if initial_all_loops == 'Active' and collect_image_cube == True:
            kpfguide['ALL_LOOPS'].write(initial_all_loops)

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
        parser = cls._add_bool_arg(parser, 'ImageCube',
            'Collect the full image cube?', default=True)
        return super().add_cmdline_args(parser, cfg)
