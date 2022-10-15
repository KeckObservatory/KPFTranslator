import ktl

from ddoitranslatormodule.KPFTranslatorFunction import KPFTranslatorFunction

from . import SetAoRotatorManual, MoveAoRotatorZero, HepaOff, AoDcsSim, SetAfmMirror, SetAfsNgs, AoHatchOpen


class SetAoForKpf(KPFTranslatorFunction):
    """
    SetAoForKpf  
        Set up AO in the safe mode for KPF operation

    SYNOPSIS
        SetAOForKPF.execute({})
    DESCRIPTION
        1. Set AO roator in Manual mode
        2. Send AO rotator to 0 deg
        3. Turn off HEPA
        4. Set AO in DCS sim mode
        5. Set AFm to Mirror
        6. Set AFS to ngs
        7. Home PCU <-- to be implemented and tested
        8. Move PCU to the KPF position <-- to be implemented and tested
        9. Open AO hatch 

    ARGUMENTS
    OPTIONS
    EXAMPLES
    
    """

    @classmethod
    def pre_condition(args, logger, cfg):
        return True

    @classmethod
    def perform(cls, args, logger, cfg):
        print('Set AO rotator to Manual')
        SetAoRotatorManual.execute({})

        print('Move AO rotator to 0 deg')
        MoveAoRotatorZero.execute({})

        print('Turn off HEPA')
        HepaOff.execute({})

        print('Set AO in DCS sim mode')
        AoDcsSim.execute({})

        print('Set AFM to Mirror')
        SetAfmMirror.execute({})

        print('Set AFS to NGS')
        SetAfsNgs.execute({})

        #print('Move PCU to Home')
        #Homepcu.execute({})

        #print('Move PCU to KPF')
        #PcuToKpf.execute({})

        print('Open AO hatch')
        AoHatchOpen.execute({})

    @classmethod
    def post_condition(cls, args, logger, cfg):
        return True