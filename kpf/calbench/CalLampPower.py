import numpy as np

import ktl

from ddoitranslatormodule.KPFTranslatorFunction import KPFTranslatorFunction
from .. import log
from . import standardize_lamp_name


class CalLampPower(KPFTranslatorFunction):
    '''Powers off one of the cal lamps via the `kpflamps` keyword service.
    '''
    @classmethod
    def pre_condition(cls, args, logger, cfg):
        # Check lamp name
        lamp = standardize_lamp_name(args.get('lamp', None))
        if lamp is None:
            return False
        # Check power
        pwr = args.get('power', None)
        if pwr is None:
            return False
        if pwr.lower() not in ['on', 'off']:
            return False
        return True

    @classmethod
    def perform(cls, args, logger, cfg):
        lamp = standardize_lamp_name(args.get('lamp'))
        pwr = args.get('power')
        log.info(f"Turning {pwr} {lamp}")
        kpflamps = ktl.cache('kpflamps')
        kpflamps[lamp].write(pwr)

    @classmethod
    def post_condition(cls, args, logger, cfg):
        lamp = standardize_lamp_name(args.get('lamp'))
        pwr = args.get('power')
        timeout = cfg.get('times', 'lamp_timeout', fallback=1)
        success = ktl.waitFor(f"($kpflamps.{lamp} == {pwr})", timeout=timeout)
        return success

    @classmethod
    def add_cmdline_args(cls, parser, cfg=None):
        '''The arguments to add to the command line interface.
        '''
        from collections import OrderedDict
        args_to_add = OrderedDict()
        args_to_add['lamp'] = {'type': str,
                               'help': 'Which lamp to control?'}
        args_to_add['power'] = {'type': str,
                                'help': 'Desired power state: "on" or "off"'}
        parser = cls._add_args(parser, args_to_add, print_only=False)
        return super().add_cmdline_args(parser, cfg)
