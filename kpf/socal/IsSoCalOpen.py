import ktl

from kpf.KPFTranslatorFunction import KPFTranslatorFunction
from kpf import (log, KPFException, FailedPreCondition, FailedPostCondition,
                 FailedToReachDestination, check_input)


class IsSoCalOpen(KPFTranslatorFunction):
    '''

    ARGS:
    =====
    None
    '''
    @classmethod
    def pre_condition(cls, args, logger, cfg):
        pass

    @classmethod
    def perform(cls, args, logger, cfg):
        timeout = args.get('timeout', 10)
        ENCSTA = ktl.cache('kpfsocal', 'ENCSTA')
        is_open = ENCSTA.waitFor("==0", timeout=timeout)
        msg = {True: 'SoCal is open', False: 'SoCal is Closed'}[is_open]
        print(msg)
        return is_open

    @classmethod
    def post_condition(cls, args, logger, cfg):
        pass

    @classmethod
    def add_cmdline_args(cls, parser, cfg=None):
        '''The arguments to add to the command line interface.
        '''
        parser.add_argument('timeout', type=float, default=10,
                            help='Timeout time in seconds')
        return super().add_cmdline_args(parser, cfg)
