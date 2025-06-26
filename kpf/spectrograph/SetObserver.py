import time
import ktl

from kpf import log, cfg
from kpf.exceptions import *
from kpf.KPFTranslatorFunction import KPFFunction, KPFScript


class SetObserver(KPFFunction):
    '''Sets the OBSERVER keyword for the science detectors in the kpfexpose
    keyword service.
    
    ARGS:
    =====
    :observer: `str` The desired value of the OBSERVER keyword.
    '''
    @classmethod
    def pre_condition(cls, args):
        check_input(args, 'observer')

    @classmethod
    def perform(cls, args):
        OBSERVER = ktl.cache('kpfexpose', 'OBSERVER')
        log.info(f"Setting OBSERVER to {args.get('observer')}")
        OBSERVER.write(args.get('observer'))

    @classmethod
    def post_condition(cls, args):
        observerval = args.get('observer')
        timeout = cfg.getfloat('times', 'kpfexpose_response_time', fallback=1)
        OBSERVER = ktl.cache('kpfexpose', 'OBSERVER')
        if OBSERVER.waitFor(f'== "{observerval}"', timeout=timeout) is not True:
            raise FailedToReachDestination(OBSERVER.read(), observerval)

    @classmethod
    def add_cmdline_args(cls, parser):
        parser.add_argument('observer', type=str,
                            help='The OBSERVER keyword')
        return super().add_cmdline_args(parser)
