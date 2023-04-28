import ktl

from kpf.KPFTranslatorFunction import KPFTranslatorFunction
from kpf import (log, KPFException, FailedPreCondition, FailedPostCondition,
                 FailedToReachDestination, check_input)


class StopTipTilt(KPFTranslatorFunction):
    '''Stop the tip tilt control loop.  This uses the ALL_LOOPS keyword to
    stop all functions including DAR (via DAR_ENABLE), tip tilt calculations
    (via TIPTILT_CALC), tip tilt control (via TIPTILT_CONTROL), offloading to
    the telescope (via OFFLOAD_DCS and OFFLOAD).
    
    ARGS:
    =====
    None
    '''
    @classmethod
    def pre_condition(cls, args, logger, cfg):
        pass

    @classmethod
    def perform(cls, args, logger, cfg):
        kpfguide = ktl.cache('kpfguide')
        kpfguide['ALL_LOOPS'].write('Inactive')

    @classmethod
    def post_condition(cls, args, logger, cfg):
        timeout = cfg.getfloat('times', 'tip_tilt_move_time', fallback=0.1)
        TIPTILT_CALC = ktl.cache('kpfguide', 'TIPTILT_CALC')
        success = TIPTILT_CALC.waitFor("== 'Inactive'")
        if success is False:
            raise FailedToReachDestination(TIPTILT_CALC.read(), 'Inactive')
        TIPTILT_CONTROL = ktl.cache('kpfguide', 'TIPTILT_CONTROL')
        success = TIPTILT_CONTROL.waitFor("== 'Inactive'")
        if success is False:
            raise FailedToReachDestination(TIPTILT_CONTROL.read(), 'Inactive')
        OFFLOAD = ktl.cache('kpfguide', 'OFFLOAD')
        success = OFFLOAD.waitFor("== 'Inactive'")
        if success is False:
            raise FailedToReachDestination(OFFLOAD.read(), 'Inactive')
