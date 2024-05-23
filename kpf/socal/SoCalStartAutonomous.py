import ktl

from kpf.KPFTranslatorFunction import KPFTranslatorFunction
from kpf import (log, KPFException, FailedPreCondition, FailedPostCondition,
                 FailedToReachDestination, check_input)


class SoCalStartAutonomous(KPFTranslatorFunction):
    '''Start SoCal's AUTONOMOUS mode by setting AUTONOMOUS=1

    ARGS:
    =====
    None
    '''
    @classmethod
    def pre_condition(cls, args, logger, cfg):
        pass

    @classmethod
    def perform(cls, args, logger, cfg):
        AUTONOMOUS = ktl.cache('kpfsocal', 'AUTONOMOUS')
        log.info('Setting kpfsocal.AUTONOMOUS = 1')
        AUTONOMOUS.write(1)

    @classmethod
    def post_condition(cls, args, logger, cfg):
        AUTONOMOUS = ktl.cache('kpfsocal', 'AUTONOMOUS')
        success = AUTONOMOUS.waitFor("==1", timeout=1)
        if success is False:
            raise FailedToReachDestination('kpfsocal.AUTONOMOUS is not 1')
