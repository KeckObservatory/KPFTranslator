import time
import ktl

from ddoitranslatormodule.KPFTranslatorFunction import KPFTranslatorFunction
from .. import (log, KPFException, FailedPreCondition, FailedPostCondition,
                FailedToReachDestination, check_input)
from .SendPCUtoHome import SendPCUtoHome


class SendPCUtoKPF(KPFTranslatorFunction):
    '''
    '''
    @classmethod
    def pre_condition(cls, args, logger, cfg):
        ao = ktl.cache('ao')
        success = ktl.waitfor("($ao.PCSFSTST == INPOS)", timeout=120)
        if success is False:
            raise FailedPreCondition('PCU is in motion')
        return True

    @classmethod
    def perform(cls, args, logger, cfg):
        # First send it home
        SendPCUtoHome.execute({})

        # Second send it to KPF
        ao = ktl.cache('ao')
        log.info(f"Sending PCU to KPF")
        ao['PCSFNAME'].write('KPF')
        shim_time = cfg.get('times', 'ao_pcu_shim_time', fallback=5)
        time.sleep(shim_time)
        timeout = cfg.get('times', 'ao_pcu_move_time', fallback=150)
        success = ktl.waitfor("($ao.PCSFSTST == INPOS)", timeout=timeout)
        if success is False:
            raise FailedToReachDestination(ao['PCSFNAME'].read(), 'KPF')

#         log.debug(f"Setting PCU to KPF Position")
#         log.debug(f'  Move PCU in LZ direction')
#         ao['PCSFLZ'].write('0')
#         time.sleep(1)
#         success = ktl.waitfor("($ao.PCSFSTST == INPOS)", timeout=120)
#         if success is False:
#             raise FailedToReachDestination(ao['PCSFLZ'].read(), 0)
#         log.debug(f'  Move PCU in X direction')
#         ao['PCSFX'].write('80')
#         time.sleep(1)
#         success = ktl.waitfor("($ao.PCSFSTST == INPOS)", timeout=120)
#         if success is False:
#             raise FailedToReachDestination(ao['PCSFX'].read(), 80)
#         log.debug(f'  Move PCU in Y direction')
#         ao['PCSFY'].write('45')
#         time.sleep(1)
#         success = ktl.waitfor("($ao.PCSFSTST == INPOS)", timeout=120)
#         if success is False:
#             raise FailedToReachDestination(ao['PCSFY'].read(), 45)

    @classmethod
    def post_condition(cls, args, logger, cfg):
        return True
