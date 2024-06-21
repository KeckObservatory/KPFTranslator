import time
import ktl

from kpf.KPFTranslatorFunction import KPFTranslatorFunction
from kpf import (log, KPFException, FailedPreCondition, FailedPostCondition,
                 FailedToReachDestination, check_input)


class SetMasterBiasToDefault(KPFTranslatorFunction):
    '''Sets the master bias file for the exposure meter to the default value

    KTL Keywords Used:

    - `kpf_expmeter.BIAS_FILE`
    '''
    @classmethod
    def pre_condition(cls, args, logger, cfg):
        pass

    @classmethod
    def perform(cls, args, logger, cfg):
        kpf_expmeter = ktl.cache('kpf_expmeter')
        default_file = '/kroot/rel/default/data/kpf_expmeter/full_bias.fits'
        log.debug(f"Setting master bias file to {default_file}")
        kpf_expmeter['BIAS_FILE'].write(default_file)

    @classmethod
    def post_condition(cls, args, logger, cfg):
        pass
