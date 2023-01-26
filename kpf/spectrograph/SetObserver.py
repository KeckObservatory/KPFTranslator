import time
import ktl

from KPFTranslatorFunction import KPFTranslatorFunction
from .. import (log, KPFException, FailedPreCondition, FailedPostCondition,
                FailedToReachDestination, check_input)


class SetObserver(KPFTranslatorFunction):
    '''Sets the OBSERVER keyword for the science detectors in the kpfexpose
    keyword service.
    
    ARGS:
    observer - The desired value of the OBSERVER keyword.
    '''
    @classmethod
    def pre_condition(cls, args, logger, cfg):
        check_input(args, 'observer')
        return True

    @classmethod
    def perform(cls, args, logger, cfg):
        kpfexpose = ktl.cache('kpfexpose')
        observer = args.get('observer')
        log.debug(f"Setting OBSERVER to '{observer}'")
        kpfexpose['OBSERVER'].write(observer)
        time_shim = cfg.get('times', 'kpfexpose_shim_time', fallback=0.1)
        time.sleep(time_shim)

    @classmethod
    def post_condition(cls, args, logger, cfg):
        observer = args.get('observer')
        timeout = cfg.get('times', 'kpfexpose_response_time', fallback=1)
        expr = f"($kpfexpose.OBSERVER == '{observer}')"
        success = ktl.waitFor(expr, timeout=timeout)
        if success is not True:
            observerkw = ktl.cache('kpfexpose', 'OBSERVER')
            raise FailedToReachDestination(observerkw.read().strip(),
                                           observer.strip())
        return True

    @classmethod
    def add_cmdline_args(cls, parser, cfg=None):
        '''The arguments to add to the command line interface.
        '''
        from collections import OrderedDict
        args_to_add = OrderedDict()
        args_to_add['observer'] = {'type': str,
                                   'help': 'The OBSERVER keyword.'}
        parser = cls._add_args(parser, args_to_add, print_only=False)
        return super().add_cmdline_args(parser, cfg)
