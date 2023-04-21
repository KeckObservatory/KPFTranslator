from datetime import datetime, timedelta

import ktl

from ddoitranslatormodule.KPFTranslatorFunction import KPFTranslatorFunction
from kpf import (log, KPFException, FailedPreCondition, FailedPostCondition,
                 FailedToReachDestination, check_input, LostTipTiltStar)


class WaitForTipTilt(KPFTranslatorFunction):
    '''
    
    ARGS:
    =====
    None
    '''
    @classmethod
    def pre_condition(cls, args, logger, cfg):
        return True

    @classmethod
    def perform(cls, args, logger, cfg):
        # See if we are locked on to the star consistently
        # First, we wait a few seconds for TIPTILT_PHASE to become "tracking"
        phase = ktl.cache('kpfguide' 'TIPTILT_PHASE')
        loop_close_time = cfg.get('times', 'tip_tilt_close_time', fallback=3)
        tracking = phase.waitFor('== Tracking', timeout=loop_close_time)
        t0 = datetime.now()
        if tracking == False:
            raise LostTipTiltStar('Unable to obtain initial lock on star')
        log.debug('Obtained initial tip tilt lock')

        # Second, wait to see if we keep lock.
        #   Keeping lock means that we are in the tracking state continuously
        #   for a tip_tilt_close_time (e.g. 3 seconds)
        max_time = cfg.get('times', 'tip_tilt_max_attempt_time', fallback=60)
        lost_lock = phase.waitFor('!= Tracking', timeout=loop_close_time)
        now = datetime.now()
        # If we didn't hold lock on the star, lets try for a moderate time 
        # (the tip_tilt_max_attempt_time) and see if we can hold it for a
        # tip_tilt_close_time during that period.
        while lost_lock == True and (now-t0).total_seconds() < max_time:
            log.debug(f'Lost lock, trying again')
            lost_lock = phase.waitFor('!= Tracking', timeout=loop_close_time)
            now = datetime.now()

        # Double check we are tracking before moving on
        tracking = phase.waitFor('== Tracking', timeout=loop_close_time)
        if tracking == False:
            raise LostTipTiltStar('Unable to hold lock on star')

    @classmethod
    def post_condition(cls, args, logger, cfg):
        return True