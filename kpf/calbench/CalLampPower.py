import numpy as np

import ktl

from kpf.KPFTranslatorFunction import KPFTranslatorFunction
from .. import (log, KPFException, FailedPreCondition, FailedPostCondition,
                FailedToReachDestination, check_input)
from . import standardize_lamp_name


class CalLampPower(KPFTranslatorFunction):
    '''Powers off one of the cal lamps via the `kpflamps` keyword service.
    
    Uses the lamp names from the OCTAGON when appropriate.
    
    Supported lamp names are:
     - BrdbandFiber
     - U_gold
     - U_daily
     - Th_daily
     - Th_gold
     - WideFlat
     - ExpMeterLED
     - CaHKLED
     - SciLED
     - SkyLED
    
    ARGS:
    lamp - name of the lamp to control
    power - "on" or "off" destination state for lamp
    '''
    @classmethod
    def pre_condition(cls, args, logger, cfg):
        # Check lamp name
        lamp = standardize_lamp_name(args.get('lamp', None))
        if lamp is None:
            msg = f"Could not standardize lamp name {args.get('lamp')}"
            raise FailedPreCondition(msg)
        # Check power
        check_input(args, 'power', allowed_values=['on', 'off'])
        return True

    @classmethod
    def perform(cls, args, logger, cfg):
        lamp = standardize_lamp_name(args.get('lamp'))
        pwr = args.get('power')
        log.debug(f"Turning {pwr} {lamp}")
        kpflamps = ktl.cache('kpflamps')
        kpflamps[lamp].write(pwr)

    @classmethod
    def post_condition(cls, args, logger, cfg):
        lamp = standardize_lamp_name(args.get('lamp'))
        pwr = args.get('power')
        timeout = cfg.get('times', 'lamp_timeout', fallback=1)
        success = ktl.waitFor(f"($kpflamps.{lamp} == {pwr})", timeout=timeout)
        if success is not True:
            kpflamps = ktl.cache('kpflamps')
            raise FailedPostCondition(kpflamps[lamp], pwr)
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
