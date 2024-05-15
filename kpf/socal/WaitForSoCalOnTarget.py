import ktl

from kpf.KPFTranslatorFunction import KPFTranslatorFunction
from kpf import (log, KPFException, FailedPreCondition, FailedPostCondition,
                 FailedToReachDestination, check_input)


class WaitForSoCalOnTarget(KPFTranslatorFunction):
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
        socal = ktl.cache('kpfsocal')
        timeout = args.get('timeout', 1)
        pyrirrad_threshold = cfg.getfloat('socal', 'pyrirrad_threshold', fallback=1000)
        expr = '($kpfsocal.ENCSTA == 0) '
        expr += 'and ($kpfsocal.EKOONLINE == Online)'
        expr += 'and ($kpfsocal.EKOMODE == 3)'
        expr += f'and ($kpfsocal.PYRIRRAD > {pyrirrad_threshold})'
        expr += 'and ($kpfsocal.AUTONOMOUS == 1)'
        expr += 'and ($kpfsocal.CAN_OPEN == True)'
        expr += 'and ($kpfsocal.IS_OPEN == True)'
        expr += 'and ($kpfsocal.IS_TRACKING == True)'
        expr += 'and ($kpfsocal.ONLINE == True)'
        expr += 'and ($kpfsocal.STATE == Tracking)'
        on_target = ktl.cache(expr, timeout=timeout)
        return on_target

    @classmethod
    def post_condition(cls, args, logger, cfg):
        pass

    @classmethod
    def add_cmdline_args(cls, parser, cfg=None):
        '''The arguments to add to the command line interface.
        '''
        parser.add_argument('timeout', type=float,
                            help='Timeout time in seconds')
        return super().add_cmdline_args(parser, cfg)
