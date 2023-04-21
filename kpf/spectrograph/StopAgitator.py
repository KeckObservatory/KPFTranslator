import time
import ktl

from kpf.KPFTranslatorFunction import KPFTranslatorFunction
from kpf import (log, KPFException, FailedPreCondition, FailedPostCondition,
                 FailedToReachDestination, check_input)


class StopAgitator(KPFTranslatorFunction):
    '''Stop the agitator motion.
    
    ARGS: None
    '''
    @classmethod
    def pre_condition(cls, args, logger, cfg):
        return True

    @classmethod
    def perform(cls, args, logger, cfg):
        agitator = ktl.cache('kpfmot', 'AGITATOR')
        if agitator.read() == 'Stopped':
            log.debug('Agitator is stopped')
        else:
            log.debug('Stopping agitator')
            agitator.write('Stop')

    @classmethod
    def post_condition(cls, args, logger, cfg):
        timeout = cfg.getfloat('times', 'agitator_startup_time', fallback=0.325)
        success = ktl.waitFor('$kpfmot.AGITATOR == Stopped', timeout=timeout)
        if success is not True:
            agitator = ktl.cache('kpfmot', 'AGITATOR')
            raise FailedToReachDestination(agitator.read(), 'Stopped')