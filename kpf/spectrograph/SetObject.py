import time
import ktl

from kpf import log, cfg
from kpf.exceptions import *
from kpf.KPFTranslatorFunction import KPFFunction, KPFScript


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
        OBJECT = ktl.cache('kpfexpose', 'OBJECT')
        obj = args.get('Object', '')
        if obj is None:
            obj = ''
        log.debug(f"Setting OBJECT to '{obj}'")
        OBJECT.write(obj)
        time_shim = cfg.getfloat('times', 'kpfexpose_shim_time', fallback=0.01)
        time.sleep(time_shim)

    @classmethod
    def post_condition(cls, args):
        obj = args.get('Object', '')
        if obj is None:
            obj = ''
        timeout = cfg.getfloat('times', 'kpfexpose_response_time', fallback=1)
        OBJECT = ktl.cache('kpfexpose', 'OBJECT')
        if OBJECT.waitFor(f"== '{obj}'", timeout=timeout) is not True:
            raise FailedToReachDestination(OBJECT.read(), obj)

    @classmethod
    def add_cmdline_args(cls, parser):
        parser.add_argument('Object', type=str,
                            help='The OBJECT keyword')
        return super().add_cmdline_args(parser)
