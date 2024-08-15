import time

import ktl

from kpf.KPFTranslatorFunction import KPFTranslatorFunction
from kpf import (log, KPFException, FailedPreCondition, FailedPostCondition,
                 FailedToReachDestination, check_input)


class EnterLowPowerMode(KPFTranslatorFunction):
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
    def pre_condition(cls, args, logger, cfg):
        log.info('Configuring KPF for Low Power Mode')
        force = args.get('force', False)
        SCRIPTNAME = ktl.cache('kpfconfig', 'SCRIPTNAME')
        SCRIPTNAME.monitor()
        if SCRIPTNAME not in ['None', '']:
            log.warning(f'A script ({SCRIPTNAME}) is running')
            if force is True:
                log.warning(f'Requesting script stop')
                kpfconfig['SCRIPTSTOP'].write('Yes')
                no_script_running = SCRIPTNAME.waitFor("==''", timeout=120)
                if no_script_running is False:
                    log.error('Script failed to stop')
                    raise FailedToReachDestination(f'{SCRIPTNAME.read()}', '')
            else:
                raise FailedPreCondition('A script is running, not setting Low Power Mode')

    @classmethod
    def perform(cls, args, logger, cfg):
        kpfconfig = ktl.cache('kpfconfig')
        kpfpower = ktl.cache('kpfpower')

        # Power down Ca HK detector systems
        kpf_hk = ktl.cache('kpf_hk')
        log.info('Disabling Ca HK detector')
        kpfconfig['CA_HK_ENABLED'].write('No')
        log.info('Turning Ca HK detector cooling off')
        kpf_hk['COOLING'].write('off')
        time.sleep(3)
        log.info('Powering off Ca HK detector systems')
        log.debug(f"Powering off {kpfpower['OUTLET_J1_NAME'].read()}")
        kpfpower['OUTLET_J1'].write('Off')
        log.debug(f"Powering off {kpfpower['OUTLET_J2_NAME'].read()}")
        kpfpower['OUTLET_J2'].write('Off')
        log.debug(f"Powering off {kpfpower['OUTLET_J5_NAME'].read()}")
        kpfpower['OUTLET_J5'].write('Off')

        # Power down CRED2 detector systems
        kpfguide = ktl.cache('kpfguide')
        log.info('Powering off CRED2 detector systems')
        kpfguide['CONTINUOUS'].write('Inactive')
        kpfguide['SAVE'].write('Inactive')
        time.sleep(2)
        log.debug(f"Powering off {kpfpower['OUTLET_K2_NAME'].read()}")
        kpfpower['OUTLET_K2'].write('Off')
        log.debug(f"Powering off {kpfpower['OUTLET_K3_NAME'].read()}")
        kpfpower['OUTLET_K3'].write('Off')


    @classmethod
    def post_condition(cls, args, logger, cfg):
        pass

    @classmethod
    def add_cmdline_args(cls, parser, cfg=None):
        parser.add_argument("--force", dest="force",
                            default=False, action="store_true",
                            help="Force change? This will terminate any running scripts.")
        return super().add_cmdline_args(parser, cfg)
