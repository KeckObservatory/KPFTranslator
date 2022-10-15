import ktl

from ddoitranslatormodule.KPFTranslatorFunction import KPFTranslatorFunction


class MoveAoRotatorZero(KPFTranslatorFunction):
    """
    MoveAoRotatorZero -- drive AO rotator to 0 deg before observing
    SYNOPSIS
        MoveAoRotatorToZero.execute()
    DESCRIPTION
        Move AO rotator to 0 deg, because TCS listenes to the LNAS rotator values

    ARGUMENTS
    OPTIONS
    EXAMPLES
    
    """

    @classmethod
    def pre_condition(args, logger, cfg):
        return True

    @classmethod
    def perform(cls, args, logger, cfg):
        ao = ktl.cache('ao')
        ao['OBRT'].write('0')
        ao['OBRTMOVE'].write('1')

    @classmethod
    def post_condition(cls, args, logger, cfg):
        ao = ktl.cache('ao')
        return ktl.waitfor('($ao.OBRTSTST == INPOS)', timeout=180)
