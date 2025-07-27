import ktl

from kpf import log, cfg
from kpf.exceptions import *
from kpf.KPFTranslatorFunction import KPFFunction, KPFScript


class UnlockFIU(KPFFunction):
    '''Unlock the FIU mechanisms

    KTL Keywords Used:

    - `kpffiu.ADC1LCK`
    - `kpffiu.ADC2LCK`
    - `kpffiu.FOLDLCK`
    - `kpffiu.HKXLCK`
    - `kpffiu.HKYLCK`
    - `kpffiu.TTXLCK`
    - `kpffiu.TTYLCK`
    '''
    @classmethod
    def pre_condition(cls, args):
        pass

    @classmethod
    def perform(cls, args):
        kpffiu = ktl.cache('kpffiu')
        kpffiu['adc1lck'].write('')
        kpffiu['adc2lck'].write('')
        kpffiu['foldlck'].write('')
        kpffiu['hkxlck'].write('')
        kpffiu['hkylck'].write('')
        kpffiu['ttxlck'].write('')
        kpffiu['ttylck'].write('')

    @classmethod
    def post_condition(cls, args):
        pass
