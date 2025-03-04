from pathlib import Path

import ktl

from kpf import log, cfg
from kpf.exceptions import *
from kpf.KPFTranslatorFunction import KPFFunction, KPFScript


class SetGuiderOutdir(KPFFunction):
    '''Set the value of the kpfguide.OUTDIR keyword

    Args:
        outdir (str): The desired output path.

    KTL Keywords Used:

    - `kpfguide.OUTDIR`
    '''
    @classmethod
    def pre_condition(cls, args):
        check_input(args, 'outdir')

    @classmethod
    def perform(cls, args):
        newoutdir = Path(args.get('outdir')).expanduser().absolute()
        kpfguide = ktl.cache('kpfguide')
        kpfguide['OUTDIR'].write(f"{newoutdir}")

    @classmethod
    def post_condition(cls, args):
        pass

    @classmethod
    def add_cmdline_args(cls, parser):
        parser.add_argument('outdir', type=str,
                            help='The desired output path')
        return super().add_cmdline_args(parser)
