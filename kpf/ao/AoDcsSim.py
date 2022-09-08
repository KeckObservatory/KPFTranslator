import ktl
from ddoitranslatormodule.KPFTranslatorFunction import KPFTranslatorFunction

class AoDcsSim(KPFTranslatorFunction):
    """
    AoDcsSim -- set AO in AO DCS sim mode, so AO doesn't communicate with telescope 
    SYNOPSIS
        AoDcsSim.execute()
    DESCRIPTION
        

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
        
        ao[AODCSSIM].write('1')
        ao[AOCOMSIM].write('1')
        ao[AODCSSFP].write('0')
        

    @classmethod
    def post_condition(cls, args, logger, cfg):
        
        ao = ktl.cache('ao')
        
        return ktl.waitfor('($ao.AODCSSIM == enabled)', timeout=3)
        return ktl.waitfor('($ao.AOCOMSIM == enabled)', timeout=3)
        return ktl.waitfor('($ao.AODCSSFP == disabled)', timeout=3)