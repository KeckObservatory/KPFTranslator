import time
import ktl

from kpf import log, cfg
from kpf.exceptions import *
from kpf.KPFTranslatorFunction import KPFFunction, KPFScript


class StopAgitator(KPFFunction):
    '''Stop the agitator motion.
    
    ARGS:
    =====
    None
    '''
    @classmethod
    def pre_condition(cls, args):
        pass

    @classmethod
    def perform(cls, args):
        agitator = ktl.cache('kpfmot', 'AGITATOR')
        if agitator.read() == 'Stopped':
            log.debug('Agitator is stopped')
        else:
            log.debug('Stopping agitator')
            try:
                agitator.write('Stop')
            except Exception as e:
                log.warning('Write to kpfmot.AGITATOR failed')
                log.debug(e)
                log.warning('Retrying')
                time.sleep(1)
                agitator.write('Stop')

    @classmethod
    def post_condition(cls, args):
        timeout = cfg.getfloat('times', 'agitator_startup_time', fallback=0.325)
        success = ktl.waitFor('$kpfmot.AGITATOR == Stopped', timeout=5*timeout)
        if success is not True:
            agitator = ktl.cache('kpfmot', 'AGITATOR')
            raise FailedToReachDestination(agitator.read(), 'Stopped')