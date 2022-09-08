import ktl
from ddoitranslatormodule.KPFTranslatorFunction import KPFTranslatorFunction


class SetAoRotatorManual(KPFTranslatorFunction):
    """
    SetAoRotatorManual -- set AO to Manual mode
    SYNOPSIS
        SetAoRotatorManual.execute()
    DESCRIPTION
        AO rotator needs to be in the Manual mode before observing.

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

        ao[OBRTDSRC].write('0')
        ao[OBRTMOVE].write('1')

    @classmethod
    def post_condition(cls, args, logger, cfg):

        ao = ktl.cache('ao')

        return ktl.waitfor('($ao.OBRTDSRC == manual)', timeout=3)
        