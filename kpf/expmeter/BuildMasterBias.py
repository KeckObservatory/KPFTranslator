import time
import ktl

from kpf.KPFTranslatorFunction import KPFTranslatorFunction
from kpf import (log, KPFException, FailedPreCondition, FailedPostCondition,
                 FailedToReachDestination, check_input)


class BuildMasterBias(KPFTranslatorFunction):
    '''
    Args:
    =====
    :: 
    '''
    @classmethod
    def pre_condition(cls, args, logger, cfg):
        check_input(args, 'files', allowed_types=[list])

    @classmethod
    def perform(cls, args, logger, cfg):

    @classmethod
    def post_condition(cls, args, logger, cfg):
        pass

    @classmethod
    def add_cmdline_args(cls, parser, cfg=None):
        '''The arguments to add to the command line interface.
        '''
        parser.add_argument('files', nargs='*',
                            help="The files to combine")
        return super().add_cmdline_args(parser, cfg)
