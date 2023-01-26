import time

import ktl

import KPFTranslatorFunction
from .. import (log, KPFException, FailedPreCondition, FailedPostCondition,
                FailedToReachDestination, check_input)
from . import register_script, obey_scriptrun, check_scriptstop, add_script_log
from ..utils.SetOutdirs import SetOutdirs
from ..spectrograph.SetProgram import SetProgram
from ..spectrograph.WaitForReady import WaitForReady
from ..utils.SetObserverFromSchedule import SetObserverFromSchedule
from ..utils.StartGUIs import StartGUIs


class StartUp(KPFTranslatorFunction):
    '''Start KPF software for afternoon setup.

    This will set the output directories, set the program ID and observers, and
    bring up the instrument GUIS.

    ARGS:
    progname - The program ID to set.  The program ID can be obtained from the
               telescope schedule:
               https://www2.keck.hawaii.edu/observing/keckSchedule/keckSchedule.php?calType=day&telnr=1&viewType=schedule
               The program ID has the format of [letter][three numbers]
    '''
    @classmethod
    @obey_scriptrun
    def pre_condition(cls, args, logger, cfg):
        check_input(args, 'progname')
        return True

    @classmethod
    def perform(cls, args, logger, cfg):
        # Set Outdirs
        expose = ktl.cache('kpfexpose', 'EXPOSE')
        if expose.read() != 'Ready':
            log.info('Waiting for kpfexpose to be Ready')
            WaitForReady.execute({})
        SetOutdirs.execute({})
        # Set progname and observer
        SetProgram.execute(args)
        SetObserverFromSchedule.execute(args)
        # Start GUIs
        StartGUIs.execute({})

    @classmethod
    def post_condition(cls, args, logger, cfg):
        return True

    @classmethod
    def add_cmdline_args(cls, parser, cfg=None):
        '''The arguments to add to the command line interface.
        '''
        from collections import OrderedDict
        args_to_add = OrderedDict()
        args_to_add['progname'] = {'type': str,
                                   'help': 'The PROGNAME keyword.'}
        parser = cls._add_args(parser, args_to_add, print_only=False)
        return super().add_cmdline_args(parser, cfg)
