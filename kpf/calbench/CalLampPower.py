import numpy as np

import ktl

from ddoitranslatormodule.KPFTranslatorFunction import KPFTranslatorFunction


def standardize_lamp_name(input_name):
    '''Take input string of a lamp name selected from the names from
    kpfcal.OCTAGON plus "WideFlat", "ExpMeterLED", "CaHKLED", "SciLED", and
    "SkyLED" and return a name which can be used in the kpflamps service.

    kpflamps keywords:
      EXPMLED = Exp Meter Back Illum LED
      FLATFIELD = Flatfield fiber
      HKLED = HK Back-Illumination LED
      OCTFLAT = Octagon flatfield
      SCILED = Science Back-Illumination LED
      SKYLED = Sky Back-Illumination LED
      TH_DAILY = ThAr Daily
      TH_GOLD = ThAr Gold
      U_DAILY = UNe Daily
      U_GOLD = UNe Gold

    octagon_names = ['BrdbandFiber', 'U_gold', 'U_daily', 'Th_daily',
                     'Th_gold', 'WideFlat']
    '''
    if input_name in [None, '']:
        return None
    lamp_name = {'BrdbandFiber': 'OCTFLAT',
                 'U_gold': 'U_GOLD',
                 'U_daily': 'U_DAILY',
                 'Th_daily': 'TH_DAILY',
                 'Th_gold': 'TH_GOLD',
                 'WideFlat': 'FLATFIELD',
                 'ExpMeterLED': 'EXPMLED',
                 'CaHKLED': 'HKLED',
                 'SciLED': 'SCILED',
                 'SkyLED': 'SKYLED',
                 }
    if input_name not in lamp_name.keys():
        return None
    lamp = lamp_name.get(input_name)
    allowed_lamps = ['EXPMLED', 'FLATFIELD', 'HKLED', 'OCTFLAT', 'SCILED',
                     'SKYLED', 'TH_DAILY', 'TH_GOLD', 'U_DAILY', 'U_GOLD']
    if lamp not in allowed_lamps:
        return None
    return lamp


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
        kpflamps = ktl.cache('kpflamps')
        kpflamps[lamp].write(pwr)

    @classmethod
    def post_condition(cls, args, logger, cfg):
        lamp = standardize_lamp_name(args.get('lamp'))
        pwr = args.get('power')
        cfg = cls._load_config(cls, cfg)
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
