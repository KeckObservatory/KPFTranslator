import subprocess

import ktl

from ddoitranslatormodule.KPFTranslatorFunction import KPFTranslatorFunction
from .. import (log, KPFException, FailedPreCondition, FailedPostCondition,
                FailedToReachDestination, check_input)
from ..ao.SetupAOforKPF import SetupAOforKPF
from ..fiu.InitializeTipTilt import InitializeTipTilt
from ..fiu.ConfigureFIU import ConfigureFIU
from .SetOutdirs import SetOutdirs
from ..spectrograph.SetProgram import SetProgram
from ..spectrograph.WaitForReady import WaitForReady
from .SetObserverFromSchedule import SetObserverFromSchedule


class StartUp(KPFTranslatorFunction):
    '''Start KPF software for afternoon setup.
    
    - Set OUTDIRS
    - Set PROGNAME
    - Set OBSERVER value based on schedule
    - bring up GUIs
    
    ARGS:
    progname - The program ID to set.
    '''
    @classmethod
    def pre_condition(cls, args, logger, cfg):
        check_input(args, 'progname')
        return True

    @classmethod
    def perform(cls, args, logger, cfg):
        # Set Outdirs
        WaitForReady.execute({})
        SetOutdirs.execute({})
        # Set progname and observer
        SetProgram.execute(args)
        SetObserverFromSchedule.execute(args)
        # Start GUIs
        log.info("Starting FIU Status GUI")
        fiugui_proc = subprocess.Popen(['/kroot/rel/default/bin/fiu_gui'])
        log.info("Starting Exposure Meter GUI")
        emgui_proc = subprocess.Popen(['/kroot/rel/default/bin/expmeter_gui'])

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
