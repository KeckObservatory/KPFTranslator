import ktl

from ddoitranslatormodule.KPFTranslatorFunction import KPFTranslatorFunction
from .. import (log, KPFException, FailedPreCondition, FailedPostCondition,
                FailedToReachDestination, check_input)


class InitializeTipTilt(KPFTranslatorFunction):
    '''Initialize the tip tilt system by setting the control mode to closed loop
    and setting the target values in X and Y to 0.
    
    ARGS: None
    '''
    @classmethod
    def pre_condition(cls, args, logger, cfg):
        return True

    @classmethod
    def perform(cls, args, logger, cfg):
        kpffiu = ktl.cache('kpffiu')
        kpffiu['TTXSRV'].write('closed')
        kpffiu['TTYSRV'].write('closed')
        kpffiu['TTXVAX'].write(0)
        kpffiu['TTYVAX'].write(0)

    @classmethod
    def post_condition(cls, args, logger, cfg):
        timeout = cfg.get('times', 'tip_tilt_move_time', fallback=0.1)
        tol = cfg.get('tolerances', 'tip_tilt_move_tolerance', fallback=0.1)
        success1 = ktl.waitFor('($kpffiu.TTXSRV == closed)', timeout=timeout)
        success2 = ktl.waitFor('($kpffiu.TTYSRV == closed)', timeout=timeout)
        success3 = ktl.waitFor(f'($kpffiu.TTXVAX <= {tol})', timeout=timeout)
        success4 = ktl.waitFor(f'($kpffiu.TTYVAX <= {tol})', timeout=timeout)
        if not success1:
            kpffiu = ktl.cache('kpffiu')
            raise FailedToReachDestination(kpffiu['TTXSRV'].read(), 'closed')
        if not success2:
            kpffiu = ktl.cache('kpffiu')
            raise FailedToReachDestination(kpffiu['TTYSRV'].read(), 'closed')
        if not success3:
            kpffiu = ktl.cache('kpffiu')
            raise FailedToReachDestination(kpffiu['TTXVAX'].read(), f"<= {tol}")
        if not success4:
            kpffiu = ktl.cache('kpffiu')
            raise FailedToReachDestination(kpffiu['TTXVAX'].read(), f"<= {tol}")
