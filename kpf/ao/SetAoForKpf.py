import ktl

from ddoitranslatormodule.KPFTranslatorFunction import KPFTranslatorFunction

from . import SetAoRotatorManual, ParkAoRotator, HepaOff, AoDcsSim, AoHatchOpen


class SetAoForKpf(KPFTranslatorFunction):
    """
    SetAoForKpf  
        Set up AO in the safe mode for KPF operation

    SYNOPSIS
        SetAOForKPF.execute({})
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
    def pre_condition(args, logger, cfg):
        return True

    @classmethod
    def perform(cls, args, logger, cfg):
        print('Set AO rotator to Manual')
        SetAoRotatorManual.execute({})

        print('Park AO rotator to 45 deg')
        ParkAoRotator.execute({})

        print('Turn off HEPA')
        HepaOff.execute({})

        print('Set AO in DCS sim mode')
        AoDcsSim.execute({})

        #print('Move PCU to KPF')

        print('Open AO hatch')
        AoHatchOpen.execute({})

    @classmethod
    def post_condition(cls, args, logger, cfg):
        return True