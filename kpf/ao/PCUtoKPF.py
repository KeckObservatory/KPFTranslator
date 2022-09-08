import ktl

from ddoitranslatormodule.KPFTranslatorFunction import KPFTranslatorFunction


class PcuToKpf(KPFTranslatorFunction):
    """
    PcuToKpf -- send PCU to the KPF location
    SYNOPSIS
        PcuToKpf.execute({})
    DESCRIPTION
        Home PCU first, then move PCU to KPF at (80, 45, 0) 

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
        print('Move PCU in LZ direction')
        ao['PCSFLZ'].write('0')
        print('Move PCU in X direction')
        ao['PCSFX'].write('80')
        print('Move PCU in Y direction')
        ao['PCSFY'].write('45')

    @classmethod
    def post_condition(cls, args, logger, cfg):
        return True