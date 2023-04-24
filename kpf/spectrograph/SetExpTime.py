import time
import ktl

from kpf.KPFTranslatorFunction import KPFTranslatorFunction
from kpf import (log, KPFException, FailedPreCondition, FailedPostCondition,
                 FailedToReachDestination, check_input)


class SetExpTime(KPFTranslatorFunction):
    '''Sets the exposure time for the science detectors in the kpfexpose
    keyword service.
    
    Args:
    ExpTime - The exposure time in seconds
    '''
    @classmethod
    def pre_condition(cls, args, logger, cfg):
        check_input(args, 'ExpTime', allowed_types=[int, float])

    @classmethod
    def perform(cls, args, logger, cfg):
        kpfexpose = ktl.cache('kpfexpose')
        exptime = args.get('ExpTime')
        log.debug(f"Setting exposure time to {exptime:.3f}")
        kpfexpose['EXPOSURE'].write(exptime)

    @classmethod
    def post_condition(cls, args, logger, cfg):
        log.debug("Checking for success")
        exptime = args.get('ExpTime')
        tol = cfg.getfloat('tolerances', 'kpfexpose_exptime_tolerance', fallback=0.01)
        timeout = cfg.getfloat('times', 'kpfexpose_response_time', fallback=1)
        expr = (f"($kpfexpose.EXPOSURE >= {exptime-tol}) and "
                f"($kpfexpose.EXPOSURE <= {exptime+tol})")
        log.debug(expr)
        success = ktl.waitFor(expr, timeout=timeout)
        if success is not True:
            exposure = ktl.cache('kpfexpose', 'EXPOSURE')
            raise FailedToReachDestination(exposure.read(), exptime)

    @classmethod
    def add_cmdline_args(cls, parser, cfg=None):
        '''The arguments to add to the command line interface.
        '''
        parser.add_argument('ExpTime', type=float,
                            help='The exposure time in seconds')
        return super().add_cmdline_args(parser, cfg)
