import ktl

from kpf.KPFTranslatorFunction import KPFTranslatorFunction
from kpf import (log, KPFException, FailedPreCondition, FailedPostCondition,
                 FailedToReachDestination, check_input)
from kpf.scripts import check_scriptstop
from kpf.calbench import standardize_lamp_name
from kpf.calbench.CalLampPower import CalLampPower


class WaitForLampWarm(KPFTranslatorFunction):
    '''Wait for the specified lamp to be warm.
    
    ARGS:
    =====
    :CalSource: The name of the lamp to wait for.
    '''
    @classmethod
    def pre_condition(cls, args, logger, cfg):
        check_input(args, 'CalSource')

    @classmethod
    def perform(cls, args, logger, cfg):
        lamp = standardize_lamp_name(args.get('CalSource'))
        lamps_that_need_warmup = ['FF_FIBER', 'BRDBANDFIBER', 'TH_DAILY',
                                  'TH_GOLD', 'U_DAILY', 'U_GOLD']
        if lamp in lamps_that_need_warmup:
            kpflamps = ktl.cache('kpflamps')
            log.debug(f'Lamp {lamp} does need to be warmed up before use')
            # Check that lamp is actually on
            lamp = standardize_lamp_name(args.get('CalSource'))
            lamp_statuskw = ktl.cache('kpflamps', f'{lamp}_STATUS')
            lamp_status = lamp_statuskw.read()
            if lamp_status == 'Off':
                log.warning(f"Lamp {lamp} is not on: {lamp_status}")
                CalLampPower.execute({'lamp': args.get('CalSource'), 'power': 'on'})
                lamp_status = lamp_statuskw.read()

            if lamp_status == 'Off':
                raise KPFException(f"Lamp {lamp} should be on: {lamp_status}")
            elif lamp_status == 'Warm':
                log.info(f"Lamp {lamp} is warm")
            elif lamp_status == 'Warming':
                lamp_timeon = kpflamps[f'{lamp}_TIMEON'].read(binary=True)
                lamp_threshold = kpflamps[f'{lamp}_THRESHOLD'].read(binary=True)
                time_to_wait = lamp_threshold - lamp_timeon
                log.info(f"Lamp {lamp} is warming")
                log.info(f"Estimated time remaining = {time_to_wait:.0f} s")
                while lamp_statuskw.read() != 'Warm':
                    # Check if scriptstop has been activated
                    check_scriptstop()
                    expr = f"($kpflamps.{lamp}_STATUS == 'Warm')"
                    warm = ktl.waitFor(expr, timeout=30)
                    if warm is False:
                        log.debug(f'Waiting for {lamp}_STATUS == Warm')
                        new_lamp_timeton = kpflamps[f'{lamp}_TIMEON'].read(binary=True)
                        if new_lamp_timeton <= lamp_timeon:
                            break
                        lamp_timeon = new_lamp_timeton

    @classmethod
    def post_condition(cls, args, logger, cfg):
        lamp = standardize_lamp_name(args.get('CalSource'))
        lamps_that_need_warmup = ['FF_FIBER', 'BRDBANDFIBER', 'TH_DAILY',
                                  'TH_GOLD', 'U_DAILY', 'U_GOLD']
        if lamp in lamps_that_need_warmup:
            lamp_statuskw = ktl.cache('kpflamps', f'{lamp}_STATUS')
            lamp_status = lamp_statuskw.read()
            if lamp_status != 'Warm':
                raise FailedPostCondition(f"Lamp {lamp} should be warm: {lamp_status}")
            else:
                log.info(f"Lamp {lamp} is warm")

    @classmethod
    def add_cmdline_args(cls, parser, cfg=None):
        '''The arguments to add to the command line interface.
        '''
        parser.add_argument('lamp', type=str,
                            choices=['BrdbandFiber', 'U_gold', 'U_daily',
                                     'Th_daily', 'Th_gold', 'WideFlat'],
                            help='Which lamp are we waiting on?')
        return super().add_cmdline_args(parser, cfg)
