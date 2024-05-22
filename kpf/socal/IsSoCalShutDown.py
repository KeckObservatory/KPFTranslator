import ktl

from kpf.KPFTranslatorFunction import KPFTranslatorFunction
from kpf import (log, KPFException, FailedPreCondition, FailedPostCondition,
                 FailedToReachDestination, check_input)


class IsSoCalShutDown(KPFTranslatorFunction):
    '''Returns True if SoCal enclosure is closed and tracker is parked.

    ARGS:
    =====
    None
    '''
    @classmethod
    def pre_condition(cls, args, logger, cfg):
        pass

    @classmethod
    def perform(cls, args, logger, cfg):
        # Enclosure
        timeout = cfg.getfloat('SoCal', 'enclosure_status_time', fallback=10)
        ENCSTA = ktl.cache('kpfsocal', 'ENCSTA')
        is_closed = ENCSTA.waitFor("==1", timeout=timeout)

        EKOHOME = ktl.cache('kpfsocal', 'EKOHOME')
        is_home = EKOHOME.waitFor("==1", timeout=timeout)

        closedstr = {True: '', False: 'NOT '}[is_closed]
        parkedstr = {True: '', False: 'NOT '}[is_home]
        msg = f'SoCal is {closedstr}closed and {parkedstr}parked'
        print(msg)

        return is_closed and is_home

    @classmethod
    def post_condition(cls, args, logger, cfg):
        pass
