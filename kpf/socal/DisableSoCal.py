import ktl

from kpf.KPFTranslatorFunction import KPFTranslatorFunction
from kpf import (log, KPFException, FailedPreCondition, FailedPostCondition,
                 FailedToReachDestination, check_input)


class DisableSoCal(KPFTranslatorFunction):
    '''Disables SoCal by setting kpfsocal.CAN_OPEN to No.

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
        log.info('Setting kpfsocal.CAN_OPEN = 0')
        CAN_OPEN.write(0)

    @classmethod
    def post_condition(cls, args, logger, cfg):
        CAN_OPEN = ktl.cache('kpfsocal', 'CAN_OPEN')
        success = CAN_OPEN.waitFor("==0", timeout=1)
        if success is False:
            raise FailedToReachDestination('kpfsocal.CAN_OPEN is not 0')
