import time

import ktl

from kpf import log, cfg
from kpf.exceptions import *
from kpf.KPFTranslatorFunction import KPFFunction, KPFScript


class EnterLowPowerMode(KPFFunction):
    '''Set KPF to a low power mode.

    This is intended for use during power outages. This reduces power use in
    the AO electronics room. We do not currently recommend any changes in the
    basement due to the sensitivity of the spectrograph to thermal changes.

    Procedure:
    - If a script is running exit or terminate it (depending on --force arg)
    - Disable HK detector
    - Stop HK cooling
    - Power off HK systems: J1, J2, J5
    - Stop CRED2 exposures (CONTINUOUS and SAVE)
    - Stop CRED2 cooling (if on)
    - Power off CRED2 (K2, K3)
    '''
    @classmethod
    def pre_condition(cls, args):
        pass

    @classmethod
    def perform(cls, args):
        kpfconfig = ktl.cache('kpfconfig')
        kpfpower = ktl.cache('kpfpower')
        kpfmon = ktl.cache('kpfmon')
        log.warning('Configuring KPF for Low Power Mode')

        # Power down Ca HK detector systems
        kpf_hk = ktl.cache('kpf_hk')
        log.warning('Disabling Ca HK detector')
        kpfconfig['CA_HK_ENABLED'].write('No')
        log.warning('Disabling HKTEMP alarm for next 24 hours')
        kpfmon['HKTEMPDIS'].write('1 day hence')
        log.warning('Turning Ca HK detector cooling off')
        kpf_hk['COOLING'].write('off')
        time.sleep(5)
        log.warning('Powering off Ca HK detector systems')
        # Wait for HK ready to avoid confusing kpfexpose EXPLAIN%
        log.warning('Waiting for kpf_hk.EXPSTATE = Ready')
        ready = kpf_hk['EXPSTATE'].waitFor("== 'Ready'", timeout=60)
        while ready == False:
            log.warning('Asking for user input')
            print()
            print("###############################################################")
            print("  Continue waiting for hpf_hk.EXPSTATE=Ready or shut down now?")
            print()
            print("  Wait (w) or Abort (a)? [w]")
            print("###############################################################")
            print()
            user_input = input()
            log.debug(f'response: "{user_input}"')
            if user_input.lower() in ['a', 'abort', 'q', 'quit']:
                return
            else:
                log.debug('Waiting for kpf_hk.EXPSTATE = Ready')
                ready = kpf_hk['EXPSTATE'].waitFor("== 'Ready'", timeout=60)

        log.warning(f"Powering off {kpfpower['OUTLET_J1_NAME'].read()}")
        kpfpower['OUTLET_J1'].write('Off')
        log.warning(f"Powering off {kpfpower['OUTLET_J2_NAME'].read()}")
        kpfpower['OUTLET_J2'].write('Off')
        log.warning(f"Disabling {kpfpower['OUTLET_J5_NAME'].read()} alarm for next 24 hours")
        kpfmon['OUTLET_J5_OODIS'].write('1 day hence')
        log.warning(f"Powering off {kpfpower['OUTLET_J5_NAME'].read()}")
        kpfpower['OUTLET_J5'].write('Off')

        # Power down CRED2 detector systems
        kpfguide = ktl.cache('kpfguide')
        log.warning('Powering off CRED2 detector systems')
        kpfguide['CONTINUOUS'].write('Inactive')
        kpfguide['SAVE'].write('Inactive')
        time.sleep(5)
        log.warning(f"Powering off {kpfpower['OUTLET_K2_NAME'].read()}")
        kpfpower['OUTLET_K2'].write('Off')
        log.warning(f"Disabling {kpfpower['OUTLET_K3_NAME'].read()} alarm for next 24 hours")
        kpfmon['OUTLET_K3_OODIS'].write('1 day hence')
        log.warning(f"Powering off {kpfpower['OUTLET_K3_NAME'].read()}")
        kpfpower['OUTLET_K3'].write('Off')


    @classmethod
    def post_condition(cls, args):
        pass
