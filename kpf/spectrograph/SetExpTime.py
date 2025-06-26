import time
import ktl

from kpf import log, cfg
from kpf.exceptions import *
from kpf.KPFTranslatorFunction import KPFFunction, KPFScript


class SetExpTime(KPFFunction):
    '''Sets the exposure time for the science detectors in the kpfexpose
    keyword service.
    
    ARGS:
    =====
    :ExpTime: `float` The exposure time in seconds
    '''
    @classmethod
    def pre_condition(cls, args):
        check_input(args, 'ExpTime', allowed_types=[int, float])

    @classmethod
    def perform(cls, args):
        EXPOSURE = ktl.cache('kpfexpose', 'EXPOSURE')
        exptime = args.get('ExpTime')
        log.debug(f"Setting exposure time to {exptime:.3f}")
        EXPOSURE.write(exptime)

    @classmethod
    def post_condition(cls, args):
        log.debug("Checking for success")
        exptime = args.get('ExpTime')
        tol = cfg.getfloat('tolerances', 'kpfexpose_exptime_tolerance', fallback=0.01)
        timeout = cfg.getfloat('times', 'kpfexpose_response_time', fallback=1)
        expr = (f"($kpfexpose.EXPOSURE >= {exptime-tol}) and "
                f"($kpfexpose.EXPOSURE <= {exptime+tol})")
        log.debug(expr)
        success = ktl.waitFor(expr, timeout=timeout)
        if success is not True:
            EXPOSURE = ktl.cache('kpfexpose', 'EXPOSURE')
            raise FailedToReachDestination(EXPOSURE.read(), exptime)

    @classmethod
    def add_cmdline_args(cls, parser):
        parser.add_argument('ExpTime', type=float,
                            help='The exposure time in seconds')
        return super().add_cmdline_args(parser)
