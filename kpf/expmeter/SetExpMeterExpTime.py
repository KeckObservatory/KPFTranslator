import time
import ktl

from kpf import log, cfg
from kpf.exceptions import *
from kpf.KPFTranslatorFunction import KPFFunction, KPFScript


class SetExpMeterExpTime(KPFFunction):
    '''Sets the exposure time for the exposure meter

    Args:
        ExpMeterExpTime (float): The exposure time in seconds.

    KTL Keywords Used:

    - `kpf_expmeter.EXPOSURE`
    '''
    @classmethod
    def pre_condition(cls, args):
        check_input(args, 'ExpMeterExpTime', allowed_types=[int, float])

    @classmethod
    def perform(cls, args):
        EXPOSURE = ktl.cache('kpf_expmeter', 'EXPOSURE')
        exptime = args.get('ExpMeterExpTime')
        log.debug(f"Setting exposure time to {exptime:.3f}")
        EXPOSURE.write(exptime)

    @classmethod
    def post_condition(cls, args):
        log.debug("Checking for success")
        exptime = args.get('ExpMeterExpTime')
        tol = cfg.getfloat('tolerances', 'kpfexpose_exptime_tolerance', fallback=0.01)
        timeout = cfg.getfloat('times', 'kpfexpose_response_time', fallback=1)
        expr = (f"($kpf_expmeter.EXPOSURE >= {exptime-tol}) and "
                f"($kpf_expmeter.EXPOSURE <= {exptime+tol})")
        log.debug(expr)
        success = ktl.waitFor(expr, timeout=timeout)
        if success is not True:
            EXPOSURE = ktl.cache('kpf_expmeter', 'EXPOSURE')
            raise FailedToReachDestination(EXPOSURE.read(), exptime)

    @classmethod
    def add_cmdline_args(cls, parser):
        parser.add_argument('ExpMeterExpTime', type=float,
                            help="The exposure time in seconds")
        return super().add_cmdline_args(parser)
