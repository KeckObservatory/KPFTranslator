import time
import ktl

from kpf import log, cfg
from kpf.exceptions import *
from kpf.KPFTranslatorFunction import KPFFunction, KPFScript


class StartAgitator(KPFFunction):
    '''Start the agitator motion and wait the appropriate startup time before
    returning.
    
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
        if AGITATOR.read() == 'Running':
            log.debug('Agitator is running')
        else:
            startup = cfg.getfloat('times', 'agitator_startup_time', fallback=0.325)
            log.debug('Starting agitator motion')
            try:
                AGITATOR.write('Run')
            except Exception as e:
                log.warning('Write to kpfmot.AGITATOR failed')
                log.debug(e)
                log.warning('Retrying')
                time.sleep(1)
                AGITATOR.write('Run')
            time.sleep(startup)

    @classmethod
    def post_condition(cls, args):
        startup = cfg.getfloat('times', 'agitator_startup_time', fallback=0.325)
        AGITATOR = ktl.cache('kpfmot', 'AGITATOR')
        if AGITATOR.waitFor('== "Running"', timeout=5*startup) is not True:
            raise FailedToReachDestination(AGITATOR.read(), 'Running')