import ktl
import time
from datetime import datetime, timedelta

from kpf.KPFTranslatorFunction import KPFTranslatorFunction
from kpf import (log, KPFException, FailedPreCondition, FailedPostCondition,
                 FailedToReachDestination, check_input)


##-----------------------------------------------------------------------------
## WaitForConfigureFIU Once
##-----------------------------------------------------------------------------
class WaitForConfigureFIUOnce(KPFTranslatorFunction):
    '''Wait for the FIU to reach specified mode (kpffiu.MODE)

    This is intended to be wrapped by :py:func:`ConfigureFIU` to handle retries.

    ARGS:
    =====
    :mode: The desired FIU mode.  One of:
           Stowed, Alignment, Acquisition, Observing, Calibration
    '''
    @classmethod
    def pre_condition(cls, args, logger, cfg):
        pass

    @classmethod
    def perform(cls, args, logger, cfg):
        dest = args.get('mode')
        kpffiu = ktl.cache('kpffiu')
        modes = kpffiu['MODE'].read()
        start = datetime.utcnow()
        move_times = [cfg.getfloat('times', 'fiu_fold_mirror_move_time', fallback=40),
                      cfg.getfloat('times', 'fiu_hatch_move_time', fallback=2)]
        end = start + timedelta(seconds=max(move_times))
        while dest.lower() not in modes.lower().split(',') and datetime.utcnow() <= end:
            time.sleep(1)
            modes = kpffiu['MODE'].read()

    @classmethod
    def post_condition(cls, args, logger, cfg):
        dest = args.get('mode')
        kpffiu = ktl.cache('kpffiu')
        modes = kpffiu['MODE'].read()
        if dest.lower() not in modes.lower().split(','):
            raise FailedToReachDestination(modes, dest)


##-----------------------------------------------------------------------------
## WaitForConfigureFIU
##-----------------------------------------------------------------------------
class WaitForConfigureFIU(KPFTranslatorFunction):
    '''Wait for the FIU to reach specified mode (kpffiu.MODE). This will retry
    the configure command if the system fails to reach its destination.
    
    ARGS:
    =====
    :mode: The desired FIU mode.  One of:
           Stowed, Alignment, Acquisition, Observing, Calibration
    '''
    @classmethod
    def pre_condition(cls, args, logger, cfg):
        keyword = ktl.cache('kpffiu', 'MODE')
        allowed_values = list(keyword._getEnumerators())
        if 'None' in allowed_values:
            allowed_values.pop(allowed_values.index('None'))
        check_input(args, 'mode', allowed_values=allowed_values)
        return True

    @classmethod
    def perform(cls, args, logger, cfg):
        dest = args.get('mode')
        try:
            WaitForConfigureFIUOnce.execute({'mode': dest})
        except FailedToReachDestination:
            log.warning(f'FIU failed to reach destination. Retrying.')
            shim_time = cfg.getfloat('times', 'fiu_mode_shim_time', fallback=0.5)
            time.sleep(shim_time)
            from .ConfigureFIU import ConfigureFIUOnce
            ConfigureFIUOnce.execute({'mode': dest, 'wait': True})

    @classmethod
    def post_condition(cls, args, logger, cfg):
        dest = args.get('mode')
        kpffiu = ktl.cache('kpffiu')
        modes = kpffiu['MODE'].read()
        if dest.lower() not in modes.lower().split(','):
            raise FailedToReachDestination(modes, dest)
        else:
            log.info(f"FIU mode is now {dest}")

    @classmethod
    def add_cmdline_args(cls, parser, cfg=None):
        '''The arguments to add to the command line interface.
        '''
        parser.add_argument('mode', type=str,
                            help='Desired mode (see kpffiu.MODE)')
        return super().add_cmdline_args(parser, cfg)

