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
        return True

    @classmethod
    def perform(cls, args, logger, cfg):
        kpfguide = ktl.cache('kpfguide')
        kpfguide['ALL_LOOPS'].write('Inactive')

    @classmethod
    def post_condition(cls, args, logger, cfg):
        kpfguide = ktl.cache('kpfguide')
        timeout = cfg.get('times', 'tip_tilt_move_time', fallback=0.1)
        expr = f"($kpfguide.TIPTILT_CALC == Inactive) "
        success = ktl.waitFor(expr, timeout=timeout)
        if success is False:
            raise FailedToReachDestination(kpfguide['TIPTILT_CALC'].read(), 'Inactive')
        expr = f"($kpfguide.TIPTILT_CONTROL == Inactive) "
        success = ktl.waitFor(expr, timeout=timeout)
        if success is False:
            raise FailedToReachDestination(kpfguide['TIPTILT_CONTROL'].read(), 'Inactive')
        expr = f"($kpfguide.OFFLOAD == Inactive) "
        success = ktl.waitFor(expr, timeout=timeout)
        if success is False:
            raise FailedToReachDestination(kpfguide['OFFLOAD'].read(), 'Inactive')
        return True