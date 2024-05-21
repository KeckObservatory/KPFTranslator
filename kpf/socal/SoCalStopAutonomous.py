import ktl

from kpf.KPFTranslatorFunction import KPFTranslatorFunction
from kpf import (log, KPFException, FailedPreCondition, FailedPostCondition,
                 FailedToReachDestination, check_input)


class SoCalStopAutonomous(KPFTranslatorFunction):
    '''

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
        log.info('Setting kpfsocal.AUTONOMOUS = 0')
        AUTONOMOUS.write(0)

    @classmethod
    def post_condition(cls, args, logger, cfg):
        AUTONOMOUS = ktl.cache('kpfsocal', 'AUTONOMOUS')
        success = AUTONOMOUS.waitFor("==0", timeout=1)
        if success is False:
            raise FailedToReachDestination('kpfsocal.AUTONOMOUS is not 0')
