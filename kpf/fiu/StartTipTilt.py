import ktl

from ddoitranslatormodule.KPFTranslatorFunction import KPFTranslatorFunction
from .. import (log, KPFException, FailedPreCondition, FailedPostCondition,
                FailedToReachDestination, check_input)


class StartTipTilt(KPFTranslatorFunction):
    '''
    
    ARGS: None
    '''
    @classmethod
    def pre_condition(cls, args, logger, cfg):
        return True

    @classmethod
    def perform(cls, args, logger, cfg):
        kpfguide = ktl.cache('kpfguide')
        kpfguide['TIPTILT_CALC'].write('Active')
        kpfguide['TIPTILT_CONTROL'].write('Active')
        kpfguide['OFFLOAD'].write('Active')

    @classmethod
    def post_condition(cls, args, logger, cfg):
        kpfguide = ktl.cache('kpfguide')
        timeout = cfg.get('times', 'tip_tilt_move_time', fallback=0.1)
        expr = f"($kpfguide.TIPTILT_CALC == Active) "
        success = ktl.waitFor(expr, timeout=timeout)
        if success is False:
            raise FailedToReachDestination(kpfguide['TIPTILT_CALC'].read(), 'Active')
        expr = f"($kpfguide.TIPTILT_CONTROL == Active) "
        success = ktl.waitFor(expr, timeout=timeout)
        if success is False:
            raise FailedToReachDestination(kpfguide['TIPTILT_CONTROL'].read(), 'Active')
        expr = f"($kpfguide.OFFLOAD == Active) "
        success = ktl.waitFor(expr, timeout=timeout)
        if success is False:
            raise FailedToReachDestination(kpfguide['OFFLOAD'].read(), 'Active')
        return True