import ktl

from kpf.KPFTranslatorFunction import KPFTranslatorFunction
from kpf import (log, KPFException, FailedPreCondition, FailedPostCondition,
                 FailedToReachDestination, check_input)


class IsSoCalClosed(KPFTranslatorFunction):
    '''Returns True if SoCal enclsoure is closed.

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
        is_closed = ENCSTA.waitFor("==1", timeout=timeout)
        msg = {True: 'SoCal is Closed', False: 'SoCal is NOT Closed'}[is_closed]
        print(msg)
        return is_closed

    @classmethod
    def post_condition(cls, args, logger, cfg):
        pass
