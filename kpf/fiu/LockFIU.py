import ktl

from kpf import log, cfg
from kpf.exceptions import *
from kpf.KPFTranslatorFunction import KPFFunction, KPFScript


class LockFIU(KPFFunction):
    '''Lock the FIU mechanisms

    Args:
        comment (str): A comment (must not be empty) designating why the
            mechanisms are locked.

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
        comment = args.get('comment', 'locked').strip()
        kpffiu = ktl.cache('kpffiu')
        kpffiu['adc1lck'].write(comment)
        kpffiu['adc2lck'].write(comment)
        kpffiu['foldlck'].write(comment)
        kpffiu['hkxlck'].write(comment)
        kpffiu['hkylck'].write(comment)
        kpffiu['ttxlck'].write(comment)
        kpffiu['ttylck'].write(comment)

    @classmethod
    def post_condition(cls, args):
        pass

    @classmethod
    def add_cmdline_args(cls, parser):
        parser.add_argument('comment', type=str,
                            help='Comment for lock keywords')
        return super().add_cmdline_args(parser)
