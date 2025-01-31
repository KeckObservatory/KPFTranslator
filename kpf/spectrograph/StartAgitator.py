import time
import ktl

from kpf import log, cfg, check_input
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
        agitator = ktl.cache('kpfmot', 'AGITATOR')
        if agitator.read() == 'Running':
            log.debug('Agitator is running')
        else:
            startup = cfg.getfloat('times', 'agitator_startup_time', fallback=0.325)
            log.debug('Starting agitator motion')
            try:
                agitator.write('Run')
            except Exception as e:
                log.warning('Write to kpfmot.AGITATOR failed')
                log.debug(e)
                log.warning('Retrying')
                time.sleep(1)
                agitator.write('Run')
            time.sleep(startup)

    @classmethod
    def post_condition(cls, args):
        startup = cfg.getfloat('times', 'agitator_startup_time', fallback=0.325)
        success = ktl.waitFor('$kpfmot.AGITATOR == Running', timeout=startup)
        if success is not True:
            agitator = ktl.cache('kpfmot', 'AGITATOR')
            raise FailedToReachDestination(agitator.read(), 'Running')