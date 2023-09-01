import time

import ktl

from kpf.KPFTranslatorFunction import KPFTranslatorFunction
from kpf import (log, KPFException, FailedPreCondition, FailedPostCondition,
                 FailedToReachDestination, check_input)


class InitializeTipTilt(KPFTranslatorFunction):
    '''Initialize the tip tilt system by setting the control mode to closed loop
    and setting the target values in X and Y to 0.
    
    ARGS:
    =====
    None
    '''
    @classmethod
    def pre_condition(cls, args, logger, cfg):
        pass

    @classmethod
    def perform(cls, args, logger, cfg):
        log.debug(f"Initializing tip tilt mirror")
        kpffiu = ktl.cache('kpffiu')
        tthome = ktl.cache('kpfguide', 'TIPTILT_HOME')
        home = tthome.read(binary=True)
        kpffiu['TTXSRV'].write('closed')
        kpffiu['TTYSRV'].write('closed')
        time.sleep(1)
        log.debug(f'Sending Tip tilt mirror to home: {home[0]} {home[1]}')
        kpffiu['TTXVAX'].write(home[0])
        kpffiu['TTYVAX'].write(home[1])

    @classmethod
    def post_condition(cls, args, logger, cfg):
        kpffiu = ktl.cache('kpffiu')
        tthome = ktl.cache('kpfguide', 'TIPTILT_HOME')
        home = tthome.read(binary=True)
        movetime = cfg.getfloat('times', 'tip_tilt_move_time', fallback=0.1)
        timeout = 1000*movetime
        tol = cfg.getfloat('tolerances', 'tip_tilt_move_tolerance', fallback=0.1)
        if not ktl.waitFor('($kpffiu.TTXSRV == closed)', timeout=timeout):
            raise FailedToReachDestination(kpffiu['TTXSRV'].read(), 'closed')
        if not ktl.waitFor('($kpffiu.TTYSRV == closed)', timeout=timeout):
            raise FailedToReachDestination(kpffiu['TTYSRV'].read(), 'closed')
        expr = (f'($kpffiu.TTXVAX >= {home[0]-tol}) and '\
                f'($kpffiu.TTXVAX <= {home[0]+tol})')
        if not ktl.waitFor(expr, timeout=timeout):
            raise FailedToReachDestination(kpffiu['TTXVAX'].read(), f"{home[0]}")
        expr = (f'($kpffiu.TTYVAX >= {home[1]-tol}) and '\
                f'($kpffiu.TTYVAX <= {home[1]+tol})')
        if not ktl.waitFor(expr, timeout=timeout):
            raise FailedToReachDestination(kpffiu['TTYVAX'].read(), f"{home[1]}")
