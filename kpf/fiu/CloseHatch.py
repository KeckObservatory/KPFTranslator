

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
        return ktl.waitFor('($kpffiu.hatch == Closed)', timeout=1)
