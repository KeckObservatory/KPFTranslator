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
    
    This script is abortable.  When the `.abort_execution()` is invoked, the
    `kpconfig.SCRIPTSTOP` is set to Yes.  This script checked for this value at
    various locations in the script.  As a result, the script will not stop
    immediately, but will stop when it reaches a breakpoint.
    '''
    @classmethod
    def pre_condition(cls, OB, logger, cfg):
        return True

    @classmethod
    def perform(cls, OB, logger, cfg):
        log.info('-------------------------')
        log.info(f"Running RunCalOB")
        log.info('-------------------------')

        if args.get('SCRIPTALLOW', False) is True:
            scriptallow = ktl.cache('kpfconfig', 'SCRIPTALLOW')
            if scriptallow.read() == 'No':
                log.warning(f"SCRIPTALLOW is No, skipping cals: {OBfile.name}")
                return False

        # Configure: Turn on Lamps
        ConfigureForCalOB.execute(OB)
        # Execute the Cal Sequence
        #   Wrap in try/except so that cleanup happens
        try:
            ExecuteCalSequence.execute(OB)
        except Exception as e:
            log.error("ExecuteCalSequence failed:")
            log.error(e)
        # Cleanup: Turn off lamps
        CleanupAfterCalOB.execute(OB)

    @classmethod
    def post_condition(cls, OB, logger, cfg):
        return True

    @classmethod
    def add_cmdline_args(cls, parser, cfg=None):
        '''The arguments to add to the command line interface.
        '''
        parser = cls._add_bool_arg(parser, 'SCRIPTALLOW',
                                   'Check the SCRIPTALLOW keyword before exeution?',
                                   default=False)
        return super().add_cmdline_args(parser, cfg)
