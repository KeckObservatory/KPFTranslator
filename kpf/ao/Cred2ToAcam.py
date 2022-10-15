import ktl

from ddoitranslatormodule.KPFTranslatorFunction import KPFTranslatorFunction


class Cred2ToAcam(KPFTranslatorFunction):
    """
    Cred2ToAcam  
        Switch CRED2 to ACAM

    SYNOPSIS
        Cred2ToAcam.execute({})
    DESCRIPTION
        1. Set AO roator in Tracking mode
        2. Set AO rotator to 45 deg
        3. Set AFM to Mirror
        4. Set AFM to ngs
        5. Move PCU to Home <-- to be implemented and tested
        

    ARGUMENTS
    OPTIONS
    EXAMPLES
    
    """

    @classmethod
    def pre_condition(args, logger, cfg):
        return True

    @classmethod
    def perform(cls, args, logger, cfg):
        
        print('Set AO rotator in Tracking and stationary')
        SetAoRotatorTracking.execute({})

        print('Set AO rotator to 45 deg')
        ParkAoRotator.execute({})

        print('Set AFM to Mirror')
        SetAfmMirror.execute({})

        print('Set AFS to NGS')
        SetAfsNgs.execute({})

        #print('Move PCU to Home')
        #HomePcu.execute({})

    @classmethod
    def post_condition(cls, args, logger, cfg):
        return True