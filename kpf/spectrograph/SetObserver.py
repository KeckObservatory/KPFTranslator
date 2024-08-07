import time
import ktl

from kpf.KPFTranslatorFunction import KPFTranslatorFunction
from kpf import (log, KPFException, FailedPreCondition, FailedPostCondition,
                 FailedToReachDestination, check_input)


class SetObserver(KPFTranslatorFunction):
    '''Sets the OBSERVER keyword for the science detectors in the kpfexpose
    keyword service.
    
    ARGS:
    =====
    :observer: `str` The desired value of the OBSERVER keyword.
    '''
    @classmethod
    def pre_condition(cls, args, logger, cfg):
        check_input(args, 'observer')

    @classmethod
    def perform(cls, args, logger, cfg):
        kpfexpose = ktl.cache('kpfexpose')
        observer = args.get('observer')
        log.info(f"Setting OBSERVER to {observer}")
        kpfexpose['OBSERVER'].write(observer)
        time_shim = cfg.getfloat('times', 'kpfexpose_shim_time', fallback=0.1)
        time.sleep(time_shim)

    @classmethod
    def post_condition(cls, args, logger, cfg):
        observer = args.get('observer')
        timeout = cfg.getfloat('times', 'kpfexpose_response_time', fallback=1)
        expr = f'($kpfexpose.OBSERVER == "{observer}")'
        success = ktl.waitFor(expr, timeout=timeout)
        if success is not True:
            observerkw = ktl.cache('kpfexpose', 'OBSERVER')
            raise FailedToReachDestination(observerkw.read().strip(),
                                           observer.strip())

    @classmethod
    def add_cmdline_args(cls, parser, cfg=None):
        parser.add_argument('observer', type=str,
                            help='The OBSERVER keyword')
        return super().add_cmdline_args(parser, cfg)
