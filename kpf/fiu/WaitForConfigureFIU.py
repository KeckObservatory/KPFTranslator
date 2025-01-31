import ktl
import time
from datetime import datetime, timedelta

from kpf import log, cfg, check_input
from kpf.exceptions import *
from kpf.KPFTranslatorFunction import KPFFunction, KPFScript
from kpf.fiu.ConfigureFIU import ConfigureFIUOnce


##-----------------------------------------------------------------------------
## WaitForConfigureFIU Once
##-----------------------------------------------------------------------------
class WaitForConfigureFIUOnce(KPFFunction):
    '''Wait for the FIU to reach specified mode (kpffiu.MODE)

    This is intended to be wrapped by :py:func:`ConfigureFIU` to handle retries.

    ARGS:
    =====
    :mode: The desired FIU mode.  One of:
           Stowed, Alignment, Acquisition, Observing, Calibration
    '''
    @classmethod
    def pre_condition(cls, args):
        keyword = ktl.cache('kpffiu', 'MODE')
        allowed_values = list(keyword._getEnumerators())
        if 'None' in allowed_values:
            allowed_values.pop(allowed_values.index('None'))
        check_input(args, 'mode', allowed_values=allowed_values)

    @classmethod
    def perform(cls, args):
        dest = args.get('mode')
        fiumode = ktl.cache('kpffiu', 'MODE')
        modes = fiumode.read()
        start = datetime.utcnow()
        move_times = [cfg.getfloat('times', 'fiu_fold_mirror_move_time', fallback=40),
                      cfg.getfloat('times', 'fiu_hatch_move_time', fallback=2)]
        end = start + timedelta(seconds=max(move_times))
        while dest.lower() not in modes.lower().split(',') and datetime.utcnow() <= end:
            time.sleep(1)
            modes = fiumode.read()
        return dest.lower() in modes.lower().split(',')

    @classmethod
    def post_condition(cls, args):
        pass


##-----------------------------------------------------------------------------
## WaitForConfigureFIU
##-----------------------------------------------------------------------------
class WaitForConfigureFIU(KPFFunction):
    '''Wait for the FIU to reach specified mode (kpffiu.MODE). This will retry
    the configure command if the system fails to reach its destination.

    Args:
        mode (str): The desired FIU mode. Allowed values: Stowed, Alignment,
            Acquisition, Observing, Calibration

    KTL Keywords Used:

    - `kpffiu.MODE`

    Scripts Called:

    - `kpf.calbench.ConfigureFIUOnce`
    '''
    @classmethod
    def pre_condition(cls, args):
        keyword = ktl.cache('kpffiu', 'MODE')
        allowed_values = list(keyword._getEnumerators())
        if 'None' in allowed_values:
            allowed_values.pop(allowed_values.index('None'))
        check_input(args, 'mode', allowed_values=allowed_values)
        return True

    @classmethod
    def perform(cls, args):
        dest = args.get('mode')
        ntries = cfg.getint('retries', 'fiu_mode_tries', fallback=2)
        shim_time = cfg.getfloat('times', 'fiu_mode_shim_time', fallback=2)
        for i in range(ntries):
            ok = WaitForConfigureFIUOnce.execute({'mode': dest})
            if ok is False:
                log.warning(f'FIU move failed on attempt {i+1} of {ntries}')
                time.sleep(shim_time)
                ConfigureFIUOnce.execute({'mode': dest, 'wait': True})
            else:
                break

    @classmethod
    def post_condition(cls, args):
        dest = args.get('mode')
        kpffiu = ktl.cache('kpffiu')
        modes = kpffiu['MODE'].read()
        if dest.lower() not in modes.lower().split(','):
            raise FailedToReachDestination(modes, dest)
        else:
            log.info(f"FIU mode is now {dest}")

    @classmethod
    def add_cmdline_args(cls, parser):
        parser.add_argument('mode', type=str,
                            choices=['Stowed', 'Alignment', 'Acquisition',
                                     'Observing', 'Calibration'],
                            help='Desired mode (see kpffiu.MODE)')
        return super().add_cmdline_args(parser)

