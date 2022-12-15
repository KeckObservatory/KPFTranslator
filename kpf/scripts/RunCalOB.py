from time import sleep
from pathlib import Path

import ktl

from ddoitranslatormodule.KPFTranslatorFunction import KPFTranslatorFunction
from .. import (log, KPFException, FailedPreCondition, FailedPostCondition,
                FailedToReachDestination, check_input)
from .ConfigureForCalOB import ConfigureForCalOB
from .ExecuteCalSequence import ExecuteCalSequence
from .CleanupAfterCalOB import CleanupAfterCalOB


class RunCalOB(KPFTranslatorFunction):
    '''Script to run a full Calibration OB from the command line.
    
    Not intended to be called by DDOI's execution engine. This script replaces
    the DDOI Script.
    '''
    abortable = True
    
    def abort_execution(args, logger, cfg):
        scriptstop = ktl.cache('kpfconfig', 'SCRIPTSTOP')
        log.warning('Abort recieved, setting kpfconfig.SCRTIPSTOP=Yes')
        scriptstop.write('Yes')
    
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
        log.info(f"Running RunCalOB")
        log.info('-------------------------')

        if args.get('SCRIPTALLOW', False) is True:
            scriptallow = ktl.cache('kpfconfig', 'SCRIPTALLOW')
            if scriptallow.read() == 'No':
                log.warning(f"SCRIPTALLOW is No, skipping cals: {OBfile.name}")
                return False

        # Configure: Turn on Lamps
        ConfigureForCalOB.execute({'OBfile': f"{OBfile}"})
        # Execute the Cal Sequence
        #   Wrap in try/except so that cleanup happens
        try:
            ExecuteCalSequence.execute({'OBfile': f"{OBfile}"})
        except Exception as e:
            log.error("ExecuteCalSequence failed:")
            log.error(e)
        # Cleanup: Turn off lamps
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

        parser = cls._add_bool_arg(parser, 'SCRIPTALLOW',
                                   'Check the SCRIPTALLOW keyword before exeution?',
                                   default=False)
        return super().add_cmdline_args(parser, cfg)
