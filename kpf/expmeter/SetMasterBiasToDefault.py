import time
import ktl

from kpf import log, cfg
from kpf.exceptions import *
from kpf.KPFTranslatorFunction import KPFFunction, KPFScript


class SetMasterBiasToDefault(KPFFunction):
    '''Sets the master bias file for the exposure meter to the default value

    KTL Keywords Used:

    - `kpf_expmeter.BIAS_FILE`
    '''
    @classmethod
    def pre_condition(cls, args):
        pass

    @classmethod
    def perform(cls, args):
        BIAS_FILE = ktl.cache('kpf_expmeter', 'BIAS_FILE')
        default_file = '/kroot/rel/default/data/kpf_expmeter/full_bias.fits'
        log.debug(f"Setting master bias file to {default_file}")
        BIAS_FILE.write(default_file)

    @classmethod
    def post_condition(cls, args):
        pass
