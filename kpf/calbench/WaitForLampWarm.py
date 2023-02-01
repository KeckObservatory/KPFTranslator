import ktl

from ddoitranslatormodule.KPFTranslatorFunction import KPFTranslatorFunction
from .. import (log, KPFException, FailedPreCondition, FailedPostCondition,
                FailedToReachDestination, check_input)
from . import standardize_lamp_name


class WaitForLampWarm(KPFTranslatorFunction):
    '''Wait for the specified lamp to be warm.
    
    ARGS:
    CalSource - The name of the lamp to wait for.
    '''
    @classmethod
    def pre_condition(cls, args, logger, cfg):
        check_input(args, 'CalSource')
        # Check that lamp is actually on
        lamp = standardize_lamp_name(args.get('CalSource'))
        lamp_status = ktl.cache('kpflamps', f'{lamp}').read()
        if lamp_status != 'On':
            raise FailedPreCondition(f"Lamp {lamp} is not on: {lamp_status}")
        return True

    @classmethod
    def perform(cls, args, logger, cfg):
        lamp = standardize_lamp_name(args.get('CalSource'))
        lamps_that_need_warmup = ['FF_FIBER', 'BRDBANDFIBER', 'TH_DAILY',
                                  'TH_GOLD', 'U_DAILY', 'U_GOLD']
        if lamp in lamps_that_need_warmup:
            kpflamps = ktl.cache('kpflamps')
            lamp_status = kpflamps[f'{lamp}_STATUS'].read()
            if lamp_status == 'Off':
                raise FailedPreCondition(f"Lamp {lamp} is not on: {lamp_status}")
            elif lamp_status == 'Warm':
                log.info(f"Lamp {lamp} is warm")
            elif lamp_status == 'Warming':
                lamp_timeon = kpflamps[f'{lamp}_TIMEON'].read(binary=True)
                lamp_threshold = kpflamps[f'{lamp}_THRESHOLD'].read(binary=True)
                time_to_wait = lamp_threshold - lamp_timeon
                log.info(f"Lamp {lamp} is warming")
                log.info(f"Estimated time remaining = {time_to_wait:.0f} s")
                expr = f"($kpfcal.{lamp}_STATUS == 'Warm')"
                success = ktl.waitFor(expr, timeout=time_to_wait+30)
                if success is False:
                    raise KPFException(f"Lamp {lamp} failed to reach warm state")

    @classmethod
    def post_condition(cls, args, logger, cfg):
        return True

    @classmethod
    def add_cmdline_args(cls, parser, cfg=None):
        '''The arguments to add to the command line interface.
        '''
        from collections import OrderedDict
        args_to_add = OrderedDict()
        args_to_add['lamp'] = {'type': str,
                               'help': 'Which lamp are we waiting for?'}
        parser = cls._add_args(parser, args_to_add, print_only=False)
        return super().add_cmdline_args(parser, cfg)
