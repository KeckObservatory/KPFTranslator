from pathlib import Path

import ktl

from kpf.KPFTranslatorFunction import KPFTranslatorFunction
from kpf import (log, KPFException, FailedPreCondition, FailedPostCondition,
                 FailedToReachDestination, check_input)


class SetGuiderOutdir(KPFTranslatorFunction):
    '''Set the value of the kpfguide.OUTDIR keyword
    
    ARGS:
    =====
    :outdir: The desired output path
    '''
    @classmethod
    def pre_condition(cls, args, logger, cfg):
        check_input(args, 'outdir')

    @classmethod
    def perform(cls, args, logger, cfg):
        newoutdir = Path(args.get('outdir')).expanduser().absolute()
        kpfguide = ktl.cache('kpfguide')
        kpfguide['OUTDIR'].write(f"{newoutdir}")

    @classmethod
    def post_condition(cls, args, logger, cfg):
        pass

    @classmethod
    def add_cmdline_args(cls, parser, cfg=None):
        '''The arguments to add to the command line interface.
        '''
        parser.add_argument('outdir', type=str,
                            help='The desired output path')
        return super().add_cmdline_args(parser, cfg)
