import time
import ktl

from KPFTranslatorFunction import KPFTranslatorFunction
from .. import (log, KPFException, FailedPreCondition, FailedPostCondition,
                FailedToReachDestination, check_input)


class SetExpMeterExptime(KPFTranslatorFunction):
    '''Sets the exposure time for the exposure meter
    
    Args:
    ExpMeterExptime - The exposure time in seconds
    '''
    @classmethod
    def pre_condition(cls, args, logger, cfg):
        check_input(args, 'ExpMeterExptime', allowed_types=[int, float])
        return True

    @classmethod
    def perform(cls, args, logger, cfg):
        kpf_expmeter = ktl.cache('kpf_expmeter')
        exptime = args.get('ExpMeterExptime')
        log.debug(f"Setting exposure time to {exptime:.3f}")
        kpf_expmeter['EXPOSURE'].write(exptime)

    @classmethod
    def post_condition(cls, args, logger, cfg):
        log.debug("Checking for success")
        exptime = args.get('ExpMeterExptime')
        tol = cfg.get('tolerances', 'kpfexpose_exptime_tolerance', fallback=0.01)
        timeout = cfg.get('times', 'kpfexpose_response_time', fallback=1)
        expr = (f"($kpf_expmeter.EXPOSURE >= {exptime-tol}) and "
                f"($kpf_expmeter.EXPOSURE <= {exptime+tol})")
        log.debug(expr)
        success = ktl.waitFor(expr, timeout=timeout)
        if success is not True:
            exposure = ktl.cache('kpf_expmeter', 'EXPOSURE')
            raise FailedToReachDestination(exposure.read(), exptime)

    @classmethod
    def add_cmdline_args(cls, parser, cfg=None):
        '''The arguments to add to the command line interface.
        '''
        from collections import OrderedDict
        args_to_add = OrderedDict()
        args_to_add['ExpMeterExptime'] = {'type': float,
                                          'help': 'The exposure time in seconds.'}
        parser = cls._add_args(parser, args_to_add, print_only=False)
        return super().add_cmdline_args(parser, cfg)
