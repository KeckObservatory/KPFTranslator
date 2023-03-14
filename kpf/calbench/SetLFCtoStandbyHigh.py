import ktl

from ddoitranslatormodule.KPFTranslatorFunction import KPFTranslatorFunction
from .. import (log, KPFException, FailedPreCondition, FailedPostCondition,
                FailedToReachDestination, check_input)


class SetLFCtoStandbyHigh(KPFTranslatorFunction):
    '''

    ARGS:
    =====
    None
    '''
    @classmethod
    def pre_condition(cls, args, logger, cfg):
        return True

    @classmethod
    def perform(cls, args, logger, cfg):
        lfc_mode = ktl.cache('kpfcal', 'OPERATIONMODE')
        log.info('Setting LFC to StandbyHigh')
        lfc_mode.write('StandbyHigh')

    @classmethod
    def post_condition(cls, args, logger, cfg):
        '''Verifies that kpfmon shows no errors.
        '''
        kpfmon = ktl.cache('kpfmon')
        expr = f"($kpfmon.LFCSTA == 'OK')"
        timeout = cfg.get('times', 'LFC_startup_time', fallback=60)
        success = ktl.waitFor(expr, timeout=timeout)
        if success is not True:
            raise FailedPostCondition('kpfmon.LFCSTA is not OK')
        return success
