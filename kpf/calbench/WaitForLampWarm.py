import ktl

from ddoitranslatormodule.KPFTranslatorFunction import KPFTranslatorFunction
from .. import log
from . import standardize_lamp_name


class WaitForLampWarm(KPFTranslatorFunction):
    '''Wait for the specified lamp to be warm.
    '''
    @classmethod
    def pre_condition(cls, args, logger, cfg):
        # Check lamp name
        lamp = standardize_lamp_name(args.get('lamp', None))
        if lamp is None:
            return False
        # Check that lamp is actually on
        kpflamps = ktl.cache('kpflamps')
        if kpflamps[lamp].read() != 'On':
            return False
        return True

    @classmethod
    def perform(cls, args, logger, cfg):
        lamp = standardize_lamp_name(args.get('lamp'))
        warmup_time = cfg.get('warmup_times', f'{lamp}_warmup_time',
                              fallback=0)
        kpflamps = ktl.cache('kpflamps')
        expr = f"($kpflamps.{lamp.upper()}_TIMEON > {warmup_time:.0f})"
        success = ktl.waitFor(expr, timeout=warmup_time*1.2)
        if success is not True:
            msg = f"The {lamp} lamp failed to reach warmup time ({warmup_time:.0f} s)"
            log.error(msg)
            raise Exception(msg)

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
                               'help': 'Which lamp to control?'}
        parser = cls._add_args(parser, args_to_add, print_only=False)
        return super().add_cmdline_args(parser, cfg)
