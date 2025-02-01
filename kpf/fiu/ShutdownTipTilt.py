import ktl

from kpf import log, cfg, check_input
from kpf.exceptions import *
from kpf.KPFTranslatorFunction import KPFFunction, KPFScript


class ShutdownTipTilt(KPFFunction):
    '''Shutdown the tip tilt system by setting the control mode to open loop
    and setting the target values in X and Y to 0.

    KTL Keywords Used:

    - `kpffiu.TTXSRV`
    - `kpffiu.TTYSRV`
    - `kpffiu.TTXVAX`
    - `kpffiu.TTYVAX`
    - `kpfguide.TIPTILT_CONTROL`
    - `kpfguide.TIPTILT_CALC`
    - `kpfguide.TIPTILT_HOME`
    '''
    @classmethod
    def pre_condition(cls, args):
        pass

    @classmethod
    def perform(cls, args):
        kpfguide = ktl.cache('kpfguide')
        kpffiu = ktl.cache('kpffiu')
        xopen = kpffiu['TTXSRV'].read() == 'Open'
        yopen = kpffiu['TTYSRV'].read() == 'Open'
        if xopen and yopen:
            # No actions needed
            return
        elif xopen == False and yopen == False:
            # Both axis are in closed loop mode
            # Shut down tip tilt activity and park mirror before opening loops
            kpfguide['TIPTILT_CONTROL'].write('Inactive')
            kpfguide['TIPTILT_CALC'].write('Inactive')
            tthome = ktl.cache('kpfguide', 'TIPTILT_HOME')
            home = tthome.read(binary=True)
            log.debug(f'Sending Tip tilt mirror to home: {home[0]} {home[1]}')
            kpffiu['TTXVAX'].write(home[0])
            kpffiu['TTYVAX'].write(home[1])
            log.debug('Opening tip tilt mirror servo loops')
            kpffiu['TTXSRV'].write('open')
            kpffiu['TTYSRV'].write('open')
        else:
            # We're in a mixed state, just open the loops
            log.debug('Opening tip tilt mirror servo loops')
            kpffiu['TTXSRV'].write('open')
            kpffiu['TTYSRV'].write('open')

    @classmethod
    def post_condition(cls, args):
        timeout = cfg.getfloat('times', 'tip_tilt_move_time', fallback=0.1)
        success1 = ktl.waitFor('($kpffiu.TTXSRV == open)', timeout=timeout)
        success2 = ktl.waitFor('($kpffiu.TTYSRV == open)', timeout=timeout)
        if success1 == False or success2 == False:
            raise FailedPostCondition(f'TT[X and/or Y]SRV did not open')
