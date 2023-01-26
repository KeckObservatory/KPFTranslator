import ktl

import KPFTranslatorFunction
from .. import (log, KPFException, FailedPreCondition, FailedPostCondition,
                FailedToReachDestination, check_input)


class WaitForTriggerFile(KPFTranslatorFunction):
    '''
    
    ARGS: None
    '''
    @classmethod
    def pre_condition(cls, args, logger, cfg):
        check_input(args, 'initial_lastfile')
        return True

    @classmethod
    def perform(cls, args, logger, cfg):
        initial_lastfile = args.get('initial_lastfile', False)
        kpfguide = ktl.cache('kpfguide')
        log.debug(f"Waiting for guider trigger file to be written out")
        # Wait for cube file to be updated
        expr = f"$kpfguide.LASTTRIGFILE != '{initial_lastfile}'"
        success = ktl.waitFor(expr, timeout=20)
        cube_file = kpfguide['LASTTRIGFILE'].read()
        log.info(f"New cube file: {cube_file}")

    @classmethod
    def post_condition(cls, args, logger, cfg):
        return True
