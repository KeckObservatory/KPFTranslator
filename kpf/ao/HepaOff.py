import ktl
from ddoitranslatormodule.KPFTranslatorFunction import KPFTranslatorFunction


class HepaOff(KPFTranslatorFunction):
    """
    hepaOff -- turn off the HEPA filter in AO before observing
    SYNOPSIS
        hepaOff.execute()
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
        ao[OBHPASTA].write('0')

    @classmethod
    def post_condition(cls, args, logger, cfg):
        
        ao = ktl.cache('ao')
        
        return ktl.waitfor('($ao.OBHPASTA == off)', timeout=3)