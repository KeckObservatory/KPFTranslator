import time
import ktl

from kpf.KPFTranslatorFunction import KPFFunction
from kpf import (log, KPFException, FailedPreCondition, FailedPostCondition,
                 FailedToReachDestination, check_input)


class SetObject(KPFFunction):
    '''Sets the OBJECT keyword for the science detectors in the kpfexpose
    keyword service.
    
    ARGS:
    =====
    :Object: `str` The desired object keyword value.
    '''
    @classmethod
    def pre_condition(cls, args):
        pass

    @classmethod
    def perform(cls, args):
        kpfexpose = ktl.cache('kpfexpose')
        obj = args.get('Object', '')
        if obj is None:
            obj = ''
        log.debug(f"Setting OBJECT to '{obj}'")
        kpfexpose['OBJECT'].write(obj)
        time_shim = cfg.getfloat('times', 'kpfexpose_shim_time', fallback=0.1)
        time.sleep(time_shim)

    @classmethod
    def post_condition(cls, args):
        obj = args.get('Object', '')
        if obj is None:
            obj = ''
        timeout = cfg.getfloat('times', 'kpfexpose_response_time', fallback=1)
        expr = f"($kpfexpose.OBJECT == '{obj}')"
        success = ktl.waitFor(expr, timeout=timeout)
        if success is not True:
            objectkw = ktl.cache('kpfexpose', 'OBJECT')
            raise FailedToReachDestination(objectkw.read(), obj)

    @classmethod
    def add_cmdline_args(cls, parser):
        parser.add_argument('Object', type=str,
                            help='The OBJECT keyword')
        return super().add_cmdline_args(parser)
