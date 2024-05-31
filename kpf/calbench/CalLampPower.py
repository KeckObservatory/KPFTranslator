import numpy as np

import ktl

from kpf.KPFTranslatorFunction import KPFTranslatorFunction
from kpf import (log, KPFException, FailedPreCondition, FailedPostCondition,
                 FailedToReachDestination, check_input)
from kpf.calbench import standardize_lamp_name


class CalLampPower(KPFTranslatorFunction):
    '''# Description
    Powers off one of the cal lamps via the `kpflamps` keyword service.

    Uses the lamp names from the OCTAGON when appropriate.

    # Parameters

    **lamp** (`str`)
    > Name of the lamp to control
    <br>Allowed Values: BrdbandFiber, U_gold, U_daily, Th_daily, Th_gold,
    WideFlat, ExpMeterLED, CaHKLED, SciLED, SkyLED

    **power** (`str`)
    > Destination state for lamp power
    <br>Allowed Values: "on" or "off"
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
        timeout = cfg.getfloat('times', 'lamp_timeout', fallback=1)
        success = ktl.waitFor(f"($kpflamps.{lamp} == {pwr})", timeout=timeout)
        if success is not True:
            kpflamps = ktl.cache('kpflamps')
            raise FailedPostCondition(kpflamps[lamp], pwr)

    @classmethod
    def add_cmdline_args(cls, parser, cfg=None):
        parser.add_argument('lamp', type=str,
                            choices=['BrdbandFiber', 'U_gold', 'U_daily',
                                     'Th_daily', 'Th_gold', 'WideFlat',
                                     'ExpMeterLED', 'CaHKLED', 'SciLED',
                                     'SkyLED'],
                            help='Which lamp to control?')
        parser.add_argument('power', type=str,
                            choices=['on', 'off'],
                            help='Desired power state: "on" or "off"')
        return super().add_cmdline_args(parser, cfg)
