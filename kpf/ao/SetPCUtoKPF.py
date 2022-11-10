import ktl

from ddoitranslatormodule.KPFTranslatorFunction import KPFTranslatorFunction
from .. import (log, KPFException, FailedPreCondition, FailedPostCondition,
                FailedToReachDestination, check_input)


class SetPCUtoKPF(KPFTranslatorFunction):
    '''
    '''
    @classmethod
    def pre_condition(cls, args, logger, cfg):
        return True

    @classmethod
    def perform(cls, args, logger, cfg):
        ao = ktl.cache('ao')
        log.debug(f"Setting PCU to KPF Position")
        log.debug(f'  Move PCU in LZ direction')
        ao['PCSFLZ'].write('0')
        success = ktl.waitfor("($ao.PCSFSTST == INPOS)", timeout=120)
        if success is False:
            raise FailedToReachDestination(ao['PCSFLZ'].read(), 0)
        log.debug(f'  Move PCU in X direction')
        ao['PCSFX'].write('80')
        success = ktl.waitfor("($ao.PCSFSTST == INPOS)", timeout=120)
        if success is False:
            raise FailedToReachDestination(ao['PCSFX'].read(), 80)
        log.debug(f'  Move PCU in Y direction')
        ao['PCSFY'].write('45')
        success = ktl.waitfor("($ao.PCSFSTST == INPOS)", timeout=120)
        if success is False:
            raise FailedToReachDestination(ao['PCSFY'].read(), 45)

    @classmethod
    def post_condition(cls, args, logger, cfg):
        z_success = ktl.waitfor('($ao.PCSFLZ == 0)', timeout=60)
        if not z_success:
            log.error(f'PCSFLZ failed to reach destination')
        x_success = ktl.waitfor('($ao.PCSFX == 80)', timeout=60)
        if not x_success:
            log.error(f'PCSFX failed to reach destination')
        y_success = ktl.waitfor('($ao.PCSFY == 45)', timeout=60)
        if not y_success:
            log.error(f'PCSFY failed to reach destination')
        return z_success and x_success and y_success
