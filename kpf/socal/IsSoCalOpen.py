import ktl

from kpf.KPFTranslatorFunction import KPFTranslatorFunction
from kpf import (log, KPFException, FailedPreCondition, FailedPostCondition,
                 FailedToReachDestination, check_input)


class IsSoCalOpen(KPFTranslatorFunction):
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
        timeout = cfg.getfloat('SoCal', 'enclosure_status_time', fallback=10)
        ENCSTA = ktl.cache('kpfsocal', 'ENCSTA')
        is_open = ENCSTA.waitFor("==0", timeout=timeout)
        msg = {True: 'SoCal is Open', False: 'SoCal is NOT Open'}[is_open]
        print(msg)
        return is_open

    @classmethod
    def post_condition(cls, args, logger, cfg):
        pass
