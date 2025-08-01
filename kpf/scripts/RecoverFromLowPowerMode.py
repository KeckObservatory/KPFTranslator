import time

import ktl

from kpf import log, cfg
from kpf.exceptions import *
from kpf.KPFTranslatorFunction import KPFFunction, KPFScript


class RecoverFromLowPowerMode(KPFFunction):
    '''Recover from low power mode.

    - Power on the Ca HK systems
    - Restore cooling to Ca HK detector
    - Re-enable Ca HK detector
    - Power on CRED2 systems

    '''
    @classmethod
    def pre_condition(cls, args):
        pass

    @classmethod
    def perform(cls, args):
        kpfconfig = ktl.cache('kpfconfig')
        kpfpower = ktl.cache('kpfpower')
        kpfmon = ktl.cache('kpfmon')
        log.warning('Recovering KPF from Low Power Mode')

        # Power up Ca HK detector systems
        kpf_hk = ktl.cache('kpf_hk')
        log.info('Powering on Ca HK detector systems')
        log.debug(f"Powering on {kpfpower['OUTLET_J1_NAME'].read()}")
        kpfpower['OUTLET_J1'].write('On')
        log.debug(f"Powering on {kpfpower['OUTLET_J2_NAME'].read()}")
        kpfpower['OUTLET_J2'].write('On')
        log.debug(f"Powering on {kpfpower['OUTLET_J5_NAME'].read()}")
        kpfpower['OUTLET_J5'].write('On')
        time.sleep(10)
        log.info('Turning Ca HK detector cooling on')
        kpf_hk['COOLING'].write('On')
        kpf_hk['COOLTARG'].write(-60)
        log.info('Enabling Ca HK detector')
        kpfconfig['CA_HK_ENABLED'].write('Yes')
        log.warning('Enabling HKTEMP alarm')
        kpfmon['HKTEMPDIS'].write(0)
        log.warning('Enabling ST_EXPOSE2 alarm')
        kpfmon['ST_EXPOSE2DIS'].write(0)
        log.warning(f"Enabling {kpfpower['OUTLET_J1_NAME'].read()} alarm")
        kpfmon['OUTLET_J1_OODIS'].write(0)
        log.warning(f"Enabling {kpfpower['OUTLET_J2_NAME'].read()} alarm")
        kpfmon['OUTLET_J2_OODIS'].write(0)
        log.warning(f"Enabling {kpfpower['OUTLET_J5_NAME'].read()} alarm")
        kpfmon['OUTLET_J5_OODIS'].write(0)

        # Power up CRED2 detector systems
        log.info('Powering on CRED2 detector systems')
        log.debug(f"Powering on {kpfpower['OUTLET_K2_NAME'].read()}")
        kpfpower['OUTLET_K2'].write('On')
        log.debug(f"Powering on {kpfpower['OUTLET_K3_NAME'].read()}")
        kpfpower['OUTLET_K3'].write('On')
        log.warning(f"Enabling {kpfpower['OUTLET_K2_NAME'].read()} alarm")
        kpfmon['OUTLET_K2_OODIS'].write(0)
        log.warning(f"Enabling {kpfpower['OUTLET_K3_NAME'].read()} alarm")
        kpfmon['OUTLET_K3_OODIS'].write(0)

    @classmethod
    def post_condition(cls, args):
        pass
