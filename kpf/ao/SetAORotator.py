import ktl

from ddoitranslatormodule.KPFTranslatorFunction import KPFTranslatorFunction


class SetAORotator(KPFTranslatorFunction):
    '''
    '''
    @classmethod
    def pre_condition(args, logger, cfg):
        return 'dest' in args.keys()

    @classmethod
    def perform(cls, args, logger, cfg):
        ao = ktl.cache('ao')
        ao['OBRT'].write(args['dest'])
        ao['OBRTMOVE'].write('1')

    @classmethod
    def post_condition(cls, args, logger, cfg):
        ao = ktl.cache('ao')
        return ktl.waitfor('($ao.OBRTSTST == INPOS)', timeout=180)
