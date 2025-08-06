import ktl

from kpf import log, cfg
from kpf.exceptions import *
from kpf.KPFTranslatorFunction import KPFFunction, KPFScript


class DisableSoCal(KPFFunction):
    '''Disables SoCal by setting kpfsocal.CAN_OPEN to No.

    KTL Keywords Used:

    - `kpfsocal.CAN_OPEN`
    '''
    @classmethod
    def pre_condition(cls, args):
        pass

    @classmethod
    def perform(cls, args):
        CAN_OPEN = ktl.cache('kpfsocal', 'CAN_OPEN')
        log.info('Setting kpfsocal.CAN_OPEN = 0')
        CAN_OPEN.write(0)

    @classmethod
    def post_condition(cls, args):
        CAN_OPEN = ktl.cache('kpfsocal', 'CAN_OPEN')
        success = CAN_OPEN.waitFor("==0", timeout=1)
        if success is False:
            raise FailedToReachDestination('kpfsocal.CAN_OPEN is not 0')
