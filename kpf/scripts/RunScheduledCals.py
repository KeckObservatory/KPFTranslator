from time import sleep
from pathlib import Path

import ktl

from ddoitranslatormodule.KPFTranslatorFunction import KPFTranslatorFunction
from .. import (log, KPFException, FailedPreCondition, FailedPostCondition,
                FailedToReachDestination, check_input)
from .ConfigureForCalOB import ConfigureForCalOB
from .RunCalOB import RunCalOB
from .CleanupAfterCalOB import CleanupAfterCalOB
from ..spectrograph.SetProgram import SetProgram
from ..spectrograph.SetObserver import SetObserver


class RunScheduledCals(KPFTranslatorFunction):
    '''Script to run cals via a cron job. Not intended to be used in other
    contexts.
    '''
    @classmethod
    def pre_condition(cls, args, logger, cfg):
        # Use file input for OB instead of args (temporary)
        check_input(args, 'OBfile')
        OBfile = Path(args.get('OBfile')).expanduser()
        return OBfile.exists()

    @classmethod
    def perform(cls, args, logger, cfg):
        OBfile = Path(args.get('OBfile')).expanduser()
        log.info('-------------------------')
        log.info(f"Running RunScheduledCals")
        log.info('-------------------------')

        scriptallow = ktl.cache('kpfconfig', 'SCRIPTALLOW')
        if scriptallow.read() == 'No':
            log.warning("SCRIPTALLOW is No, skipping scheduled cals: {OBfile.name}")
        else:
            SetProgram.execute({'progname': ''})
            SetObserver.execute({'observer': 'None'})
            ConfigureForCalOB.execute({'OBfile': f"{OBfile}"})
            RunCalOB.execute({'OBfile': f"{OBfile}"})
            CleanupAfterCalOB.execute({'OBfile': f"{OBfile}"})

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
