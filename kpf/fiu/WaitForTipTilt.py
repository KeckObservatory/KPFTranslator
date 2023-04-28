from datetime import datetime, timedelta

import ktl

from kpf.KPFTranslatorFunction import KPFTranslatorFunction
from kpf import (log, KPFException, FailedPreCondition, FailedPostCondition,
                 FailedToReachDestination, check_input, LostTipTiltStar)


class WaitForTipTilt(KPFTranslatorFunction):
    '''Attempts to determine whether tip tilt loops have started successfully.

    This logic is just meant to put some basic starting checks on the system to
    see if it started up successfully before we initiate an observation. This
    does not replace human monitoring of the loops during an exposure.

    There are two time scales used here: tip_tilt_close_time and
    tip_tilt_max_attempt_time:

    tip_tilt_close_time is typically small (e.g. 3 seconds) an is there to make
    sure that if the tracking phase becomes "tracking", this it isn't a
    transitory event.

    tip_tilt_max_attempt_time is typically larger (e.g. 60 seconds) and it is
    how long the system will try to obtain a lock before giving up and erroring
    out.

    First, the system waits up to tip_tilt_close_time for the phase to become
    "tracking".  If it is unable to attain the tracking state within that time,
    it raises an error.

    If we do attain an initial tracking lock, we want to see if the system holds
    it and it was not transitory. To do so, the system will wait for one more
    tip_tilt_close_time period and will declare success if the system does not
    transition away from "tracking" during that period.

    If we do lose lock during that period, it will keep trying to meet that
    second criteria for a period of tip_tilt_max_attempt_time after the initial
    tracking lock.

    ARGS:
    =====
    None
    '''
    @classmethod
    def pre_condition(cls, args, logger, cfg):
        return True

    @classmethod
    def perform(cls, args, logger, cfg):

        # Now see if we are locked on to the star consistently
        # First, we wait a few seconds for TIPTILT_PHASE to become "tracking"
        phase = ktl.cache('kpfguide', 'TIPTILT_PHASE')
        loop_close_time = cfg.get('times', 'tip_tilt_close_time', fallback=3)
        tracking = phase.waitFor('== "Tracking"', timeout=loop_close_time)
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

        # Double check we are tracking before moving on
        if lost_lock == True:
            raise LostTipTiltStar('Unable to hold lock on star')

    @classmethod
    def post_condition(cls, args, logger, cfg):
        pass