from datetime import datetime, timedelta

import ktl

from kpf.KPFTranslatorFunction import KPFTranslatorFunction
from kpf import (log, KPFException, FailedPreCondition, FailedPostCondition,
                 FailedToReachDestination, check_input, LostTipTiltStar)


class StartTipTilt(KPFTranslatorFunction):
    '''Start the tip tilt control loop.  This uses the ALL_LOOPS keyword to
    start all functions including DAR (via DAR_ENABLE), tip tilt calculations
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
        log.debug(f'Ensuring kpfguide.DAR_ENABLE is yes')
        kpfguide['DAR_ENABLE'].write('Yes')
        log.info('Turning kpfguide.ALL_LOOPS on')
        kpfguide['ALL_LOOPS'].write('Active')

        # Now see if we are locked on to the star consistently
        # First, we wait a few seconds for TIPTILT_PHASE to become "tracking"
        phase = ktl.cache('kpfguide' 'TIPTILT_PHASE')
        loop_close_time = cfg.get('times', 'tip_tilt_close_time', fallback=3)
        tracking = phase.waitFor('== Tracking', timeout=loop_close_time)
        t0 = datetime.now()
        if tracking == False:
            raise LostTipTiltStar('Unable to obtain initial lock on star')
        else:
            log.debug('Obtained initial tip tilt lock')
            # Second, wait a few seconds to see if we keep lock
            max_attempt_time = cfg.get('times', 'tip_tilt_max_attempt_time', fallback=60)
            lost_lock = phase.waitFor('!= Tracking', timeout=loop_close_time)
            now = datetime.now()
            # If we didn't hold on to the star, lets try a little while longer
            while lost_lock == True and (now-t0).total_seconds() < max_attmpt_time:
                log.debug(f'Lost lock, trying again')
                lost_lock = phase.waitFor('!= Tracking', timeout=loop_close_time)
        tracking = phase.waitFor('== Tracking', timeout=loop_close_time)
        if tracking == False:
            raise LostTipTiltStar('Unable to hold lock on star')

    @classmethod
    def post_condition(cls, args, logger, cfg):
        kpfguide = ktl.cache('kpfguide')
        timeout = cfg.getfloat('times', 'tip_tilt_move_time', fallback=0.1)
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
