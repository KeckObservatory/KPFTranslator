import time
import ktl

from ddoitranslatormodule.KPFTranslatorFunction import KPFTranslatorFunction
from .. import (log, KPFException, FailedPreCondition, FailedPostCondition,
                FailedToReachDestination, check_input)


class StartAgitator(KPFTranslatorFunction):
    '''Start the agitator motion and wait the appropriate startup time before
    returning.
    
    ARGS: None
    '''
    @classmethod
    def pre_condition(cls, args, logger, cfg):
        return True

    @classmethod
    def perform(cls, args, logger, cfg):
        agitator = ktl.cache('kpfmot', 'AGITATOR')
        if agitator.read() == 'Running':
            log.debug('Agitator is running')
        else:
            startup = cfg.get('times', 'agitator_startup_time', fallback=0.325)
            log.debug('Starting agitator motion')
            agitator.write('Run')
            time.sleep(startup)

    @classmethod
    def post_condition(cls, args, logger, cfg):
        startup = cfg.get('times', 'agitator_startup_time', fallback=0.325)
        success = ktl.waitFor('$kpfmot.AGITATOR == Running', timeout=startup)
        if success is not True:
            agitator = ktl.cache('kpfmot', 'AGITATOR')
            raise FailedToReachDestination(agitator.read(), 'Running')