

import ktl

from ddoitranslatormodule.KPFTranslatorFunction import KPFTranslatorFunction


class OpenHatch(KPFTranslatorFunction):
    '''Open the FIU hatch
    '''
    @classmethod
    def pre_condition(cls, args, logger, cfg):
        return True

    @classmethod
    def perform(cls, args, logger, cfg):
        kpffiu = ktl.cache('kpffiu')
        kpffiu['HATCH'].write('Open')

    @classmethod
    def post_condition(cls, args, logger, cfg):
        cfg = cls._load_config(cls, cfg)
        timeout = cfg.get('expected_times', 'fiu_hatch_move_time', fallback=1)
        return ktl.waitFor('($kpffiu.hatch == Open)', timeout=timeout)
