import numpy as np

import ktl

from ddoitranslatormodule.KPFTranslatorFunction import KPFTranslatorFunction


class CalLampPower(KPFTranslatorFunction):
    '''Powers off one of the cal lamps via the `kpflamps` keyword service.
    
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
    '''
    @classmethod
    def pre_condition(cls, args, logger, cfg):
        lamp = args.get('lamp', None)
        if lamp is None:
            return False
        allowed_lamps = ['EXPMLED', 'FLATFIELD', 'HKLED', 'OCTFLAT', 'SCILED',
                         'SKYLED', 'TH_DAILY', 'TH_GOLD', 'U_DAILY', 'U_GOLD']
        if lamp not in allowed_lamps:
            return False
        pwr = args.get('power', None)
        if pwr is None:
            return False
        if pwr.lower() not in ['on', 'off']:
            return False
        return True

    @classmethod
    def perform(cls, args, logger, cfg):
        lamp = args.get('lamp')
        pwr = args.get('power')
        kpflamps = ktl.cache('kpflamps')
        kpflamps["{lamp}"].write(pwr)

    @classmethod
    def post_condition(cls, args, logger, cfg):
        lamp = args.get('lamp')
        pwr = args.get('power')
        cfg = cls._load_config(cls, cfg)
        timeout = cfg.get('times', 'lamp_timeout', fallback=1)
        success = ktl.waitFor(f"($kpflamps.{lamp} == {pwr})", timeout=timeout)
        return success

    @classmethod
    def add_cmdline_args(cls, parser, cfg=None):
        args_to_add = OrderedDict()
        args_to_add['lamp'] = {'type': str,
                               'help': 'Which lamp to control?'}
        args_to_add['power'] = {'type': str,
                                'help': 'Desired power state: "on" or "off"'}
        parser = cls._add_args(parser, args_to_add, print_only=False)
        return super().add_cmdline_args(parser, cfg)
