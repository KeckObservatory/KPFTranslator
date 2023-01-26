import ktl

from KPFTranslatorFunction import KPFTranslatorFunction


class ShutdownTipTilt(KPFTranslatorFunction):
    '''Shutdown the tip tilt system by setting the control mode to open loop
    and setting the target values in X and Y to 0.
    
    ARGS: None
    '''
    @classmethod
    def pre_condition(cls, args, logger, cfg):
        return True

    @classmethod
    def perform(cls, args, logger, cfg):
        kpfguide = ktl.cache('kpfguide')
        kpfguide['TIPTILT_CONTROL'].write('Inactive')
        kpfguide['TIPTILT_CALC'].write('Inactive')
        kpffiu = ktl.cache('kpffiu')
        kpffiu['TTXVAX'].write(0)
        kpffiu['TTYVAX'].write(0)
        kpffiu['TTXSRV'].write('open')
        kpffiu['TTYSRV'].write('open')

    @classmethod
    def post_condition(cls, args, logger, cfg):
        timeout = cfg.get('times', 'tip_tilt_move_time', fallback=0.1)
        success1 = ktl.waitFor('($kpffiu.TTXSRV == open)', timeout=timeout)
        success2 = ktl.waitFor('($kpffiu.TTYSRV == open)', timeout=timeout)
        return success1 and success2