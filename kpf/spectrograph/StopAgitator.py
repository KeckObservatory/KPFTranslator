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
        AGITATOR = ktl.cache('kpfmot', 'AGITATOR')
        if AGITATOR.read() == 'Stopped':
            log.debug('Agitator is stopped')
        else:
            log.debug('Stopping agitator')
            try:
                AGITATOR.write('Stop')
            except Exception as e:
                log.warning('Write to kpfmot.AGITATOR failed')
                log.debug(e)
                log.warning('Retrying')
                time.sleep(1)
                AGITATOR.write('Stop')

    @classmethod
    def post_condition(cls, args):
        startup = cfg.getfloat('times', 'agitator_startup_time', fallback=0.325)
        AGITATOR = ktl.cache('kpfmot', 'AGITATOR')
        if AGITATOR.waitFor('== "Stopped"', timeout=5*startup) is not True:
            raise FailedToReachDestination(AGITATOR.read(), 'Stopped')
