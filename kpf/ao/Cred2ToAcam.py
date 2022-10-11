import ktl

from ddoitranslatormodule.KPFTranslatorFunction import KPFTranslatorFunction


class Cred2ToAcam(KPFTranslatorFunction):
    """
    Cred2ToAcam  
        Switch CRED2 to ACAM

    SYNOPSIS
        Cred2ToAcam.execute({})
    DESCRIPTION
        1. Set AO roator in Manual mode
        2. Park AO rotator to 45 deg
        3. Turn off HEPA
        4. Set AO in DCS sim mode
        5. Move PCU to the KPF position <-- to be implemented
        6. Open AO hatch 

    ARGUMENTS
    OPTIONS
    EXAMPLES
    
    """

    @classmethod
    def pre_condition(cls, args, logger, cfg):
        return True

    @classmethod
    def perform(cls, args, logger, cfg):
        ao = ktl.cache('ao')
        raise NotImplementedError()

    @classmethod
    def post_condition(cls, args, logger, cfg):
        return True