

import ktl

from ddoitranslatormodule.KPFTranslatorFunction import KPFTranslatorFunction


class FoldMirrorOut(KPFTranslatorFunction):
    '''Move the FIU fold mirror out of the beam
    '''
    @classmethod
    def pre_condition(cls, args, logger, cfg):
        return True

    @classmethod
    def perform(cls, args, logger, cfg):
        kpffiu = ktl.cache('kpffiu')
        kpffiu['FOLDNAM'].write('out')

    @classmethod
    def post_condition(cls, args, logger, cfg):
        cfg = cls._load_config(cls, cfg)
        timeout = cfg.get('times', 'fiu_fold_mirror_move_time', fallback=5)
        return ktl.waitFor('($kpffiu.foldnam == out)', timeout=timeout)
