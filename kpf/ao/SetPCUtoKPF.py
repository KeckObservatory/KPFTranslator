import ktl

from ddoitranslatormodule.KPFTranslatorFunction import KPFTranslatorFunction


class SetPCUtoKPF(KPFTranslatorFunction):
    """
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
        ao = ktl.cache('ao')

        z_success = ktl.waitfor('($ao.PCSFLZ == 0)', timeout=60)
        if not z_success:
            print(f'PCSFLZ failed to reach destination')

        x_success = ktl.waitfor('($ao.PCSFX == 80)', timeout=60)
        if not x_success:
            print(f'PCSFX failed to reach destination')

        y_success = ktl.waitfor('($ao.PCSFY == 45)', timeout=60)
        if not y_success:
            print(f'PCSFY failed to reach destination')

        return z_success and x_success and y_success