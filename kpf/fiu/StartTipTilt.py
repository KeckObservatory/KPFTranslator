import time
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

    KTL Keywords Used:

    - `kpffiu.TTXSRV`
    - `kpffiu.TTYSRV`
    - `kpfguide.DAR_ENABLE`
    - `kpfguide.ALL_LOOPS`
    '''
    @classmethod
    def pre_condition(cls, args, logger, cfg):
        pass

    @classmethod
    def perform(cls, args, logger, cfg):
        expr = "($kpffiu.TTXSRV == 'Closed') and ($kpffiu.TTYSRV == 'Closed')"
        servo_loops_closed = ktl.waitFor(expr, timeout=0.5)
        if not servo_loops_closed:
            kpffiu = ktl.cache('kpffiu')
            log.info('Closing servo loops')
            kpffiu['TTXSRV'].write('Closed')
            kpffiu['TTYSRV'].write('Closed')
            movetime = cfg.getfloat('times', 'tip_tilt_move_time', fallback=0.1)
            time.sleep(10*movetime)

        kpfguide = ktl.cache('kpfguide')
        log.info('Turning kpfguide.ALL_LOOPS on')
        kpfguide['ALL_LOOPS'].write('Active')

    @classmethod
    def post_condition(cls, args, logger, cfg):
        pass
