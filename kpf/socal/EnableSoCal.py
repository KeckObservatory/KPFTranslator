import ktl

from kpf.KPFTranslatorFunction import KPFTranslatorFunction
from kpf import (log, KPFException, FailedPreCondition, FailedPostCondition,
                 FailedToReachDestination, check_input)


class EnableSoCal(KPFTranslatorFunction):
    '''Enables SoCal by setting kpfsocal.CAN_OPEN to Yes.

    ARGS:
    =====
    None
    '''
    @classmethod
    def pre_condition(cls, args, logger, cfg):
        pass

    @classmethod
    def perform(cls, args, logger, cfg):
        CAN_OPEN = ktl.cache('kpfsocal', 'CAN_OPEN')
        log.info('Setting kpfsocal.CAN_OPEN = 1')
        CAN_OPEN.write(1)

    @classmethod
    def post_condition(cls, args, logger, cfg):
        CAN_OPEN = ktl.cache('kpfsocal', 'CAN_OPEN')
        success = CAN_OPEN.waitFor("==1", timeout=1)
        if success is False:
            raise FailedToReachDestination('kpfsocal.CAN_OPEN is not 1')
