import ktl

from kpf.KPFTranslatorFunction import KPFTranslatorFunction
from kpf import (log, KPFException, FailedPreCondition, FailedPostCondition,
                 FailedToReachDestination, check_input)


class LockFIU(KPFTranslatorFunction):
    '''Lock the FIU mechanisms
    
    ARGS:
    =====
    :comment: - A comment (must not be empty) designating why the mechanisms
                are locked.
    '''
    @classmethod
    def pre_condition(cls, args, logger, cfg):
        pass

    @classmethod
    def perform(cls, args, logger, cfg):
        comment = args.get('comment', 'locked').strip()
        kpffiu = ktl.cache('kpffiu')
        kpffiu['adc1lck'].write(comment)
        kpffiu['adc2lck'].write(comment)
        kpffiu['foldlck'].write(comment)
        kpffiu['hkxlck='].write(comment)
        kpffiu['hkylck='].write(comment)
        kpffiu['ttxlck='].write(comment)
        kpffiu['ttylck='].write(comment)

    @classmethod
    def post_condition(cls, args, logger, cfg):
        pass

    @classmethod
    def add_cmdline_args(cls, parser, cfg=None):
        '''The arguments to add to the command line interface.
        '''
        parser.add_argument('comment', type=str,
                            help='Comment for lock keywords')
        return super().add_cmdline_args(parser, cfg)
