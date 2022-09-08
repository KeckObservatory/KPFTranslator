import ktl

from ddoitranslatormodule.KPFTranslatorFunction import KPFTranslatorFunction


class ParkAoRotator(KPFTranslatorFunction):
    """
    parkAoRotator -- park AO rotator at 45 deg before observing
    SYNOPSIS
        parkAoRotator.execute()
    DESCRIPTION
        Check if the HEPA filter inside the AO enclosure is turned off
        before observing. If not, turn it off.
        set ao.OBHPAON=0

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
        ao['OBRTNAME'].write('45')
        ao['OBRTMOVE'].write('1')

    @classmethod
    def post_condition(cls, args, logger, cfg):
        ao = ktl.cache('ao')
        return ktl.waitfor('($ao.OBRTSTST == INPOS)', timeout=180)
