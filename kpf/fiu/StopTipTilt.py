import ktl

from kpf import log, cfg
from kpf.exceptions import *
from kpf.KPFTranslatorFunction import KPFFunction, KPFScript


class StopTipTilt(KPFFunction):
    '''Stop the tip tilt control loop.  This uses the ALL_LOOPS keyword to
    stop all functions including DAR (via DAR_ENABLE), tip tilt calculations
    (via TIPTILT_CALC), tip tilt control (via TIPTILT_CONTROL), offloading to
    the telescope (via OFFLOAD_DCS and OFFLOAD).

    KTL Keywords Used:

    - `kpfguide.TIPTILT_CALC`
    - `kpfguide.TIPTILT_CONTROL`
    - `kpfguide.OFFLOAD`
    - `kpfguide.ALL_LOOPS`
    '''
    @classmethod
    def pre_condition(cls, args):
        pass

    @classmethod
    def perform(cls, args):
        ALL_LOOPS = ktl.cache('kpfguide', 'ALL_LOOPS')
        ALL_LOOPS.write('Inactive')

    @classmethod
    def post_condition(cls, args):
        timeout = cfg.getfloat('times', 'tip_tilt_move_time', fallback=0.1)
        TIPTILT_CALC = ktl.cache('kpfguide', 'TIPTILT_CALC')
        if TIPTILT_CALC.waitFor("== 'Inactive'") is False:
            raise FailedToReachDestination(TIPTILT_CALC.read(), 'Inactive')
        TIPTILT_CONTROL = ktl.cache('kpfguide', 'TIPTILT_CONTROL')
        if TIPTILT_CONTROL.waitFor("== 'Inactive'") is False:
            raise FailedToReachDestination(TIPTILT_CONTROL.read(), 'Inactive')
        OFFLOAD = ktl.cache('kpfguide', 'OFFLOAD')
        if OFFLOAD.waitFor("== 'Inactive'") is False:
            raise FailedToReachDestination(OFFLOAD.read(), 'Inactive')
