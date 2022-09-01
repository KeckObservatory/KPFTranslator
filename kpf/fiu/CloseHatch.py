

import ktl

from ddoitranslatormodule.KPFTranslatorFunction import KPFTranslatorFunction


class CloseHatch(KPFTranslatorFunction):
    '''Close the FIU hatch
    '''
    @classmethod
    def pre_condition(cls, args, logger, cfg):
        return True

    @classmethod
    def perform(cls, args, logger, cfg):
        kpffiu = ktl.cache('kpffiu')
        kpffiu['HATCH'].write('Closed')

    @classmethod
    def post_condition(cls, args, logger, cfg):
        cfg = cls._load_config(cls, cfg)
        timeout = cfg['expected_times'].get('fiu_hatch_move_time', 1)
        return ktl.waitFor('($kpffiu.hatch == Closed)', timeout=timeout)
