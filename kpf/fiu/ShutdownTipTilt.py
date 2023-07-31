import ktl

from kpf.KPFTranslatorFunction import KPFTranslatorFunction
from kpf import (log, KPFException, FailedPreCondition, FailedPostCondition,
                 FailedToReachDestination, check_input)


class ShutdownTipTilt(KPFTranslatorFunction):
    '''Shutdown the tip tilt system by setting the control mode to open loop
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
        kpfguide = ktl.cache('kpfguide')
        kpfguide['TIPTILT_CONTROL'].write('Inactive')
        kpfguide['TIPTILT_CALC'].write('Inactive')
        kpffiu = ktl.cache('kpffiu')
        tthome = ktl.cache('kpfguide', 'TIPTILT_HOME')
        home = tthome.read(binary=True)
        log.debug(f'Sending Tip tilt mirror to home: {home[0]} {home[1]}')
        kpffiu['TTXVAX'].write(home[0])
        kpffiu['TTYVAX'].write(home[1])
        log.info('Opening tip tilt mirror servo loops')
        kpffiu['TTXSRV'].write('open')
        kpffiu['TTYSRV'].write('open')

    @classmethod
    def post_condition(cls, args, logger, cfg):
        timeout = cfg.getfloat('times', 'tip_tilt_move_time', fallback=0.1)
        success1 = ktl.waitFor('($kpffiu.TTXSRV == open)', timeout=timeout)
        success2 = ktl.waitFor('($kpffiu.TTYSRV == open)', timeout=timeout)
        if success1 == False or success2 == False:
            raise FailedPostCondition(f'TT{X,Y}SRV did not open')
