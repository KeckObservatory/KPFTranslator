import time
import ktl

from kpf.KPFTranslatorFunction import KPFTranslatorFunction
from kpf import (log, KPFException, FailedPreCondition, FailedPostCondition,
                 FailedToReachDestination, check_input, KPFQuietException)


##-----------------------------------------------------------------------------
## Configure FIU Once
##-----------------------------------------------------------------------------
class ConfigureFIUOnce(KPFTranslatorFunction):
    '''Set the FIU mode (kpffiu.MODE) with a single attempt.
    
    This is intended to be wrapped by :py:func:`ConfigureFIU` to handle retries.
    '''
    @classmethod
    def pre_condition(cls, args, logger, cfg):
        return True

    @classmethod
    def perform(cls, args, logger, cfg):
        dest = args.get('mode')
        kpffiu = ktl.cache('kpffiu')
        log.debug(f"Setting FIU mode to {dest}")
        kpffiu['MODE'].write(dest, wait=args.get('wait', True))
        shim_time = cfg.getfloat('times', 'fiu_mode_shim_time', fallback=5)
        time.sleep(shim_time)
        # Hack to check here and return result
        # It seems like the CLI sees this exception even though it is caught by
        # the ConfigureFIU code, so we'll not raise an exception and we'll
        # instead return a status from this
        modes = kpffiu['MODE'].read()
        if dest.lower() not in modes.lower().split(','):
            msg = f"FIU reached {modes} while trying to reach {dest}"
            log.warning(msg)
            return False
        else:
            return True

    @classmethod
    def post_condition(cls, args, logger, cfg):
        pass
#         dest = args.get('mode')
#         kpffiu = ktl.cache('kpffiu')
#         modes = kpffiu['MODE'].read()
#         if dest.lower() not in modes.lower().split(','):
#             msg = f"FIU reached {modes} while trying to reach {dest}"
#             raise KPFQuietException(msg)
#         return True


##-----------------------------------------------------------------------------
## Configure FIU
##-----------------------------------------------------------------------------
class ConfigureFIU(KPFTranslatorFunction):
    '''Set the FIU mode (kpffiu.MODE). This will retry if the first attempt
    fails.
    
    ARGS:
    =====
    :mode: The desired FIU mode.  One of:
           Stowed, Alignment, Acquisition, Observing, Calibration
    :wait: (bool) Wait for move to complete before returning? (default: True)
    '''
    @classmethod
    def pre_condition(cls, args, logger, cfg):
        keyword = ktl.cache('kpffiu', 'MODE')
        allowed_values = list(keyword._getEnumerators())
        if 'None' in allowed_values:
            allowed_values.pop(allowed_values.index('None'))
        check_input(args, 'mode', allowed_values=allowed_values)

    @classmethod
    def perform(cls, args, logger, cfg):
        dest = args.get('mode')
        ntries = cfg.getint('retries', 'fiu_mode_tries', fallback=2)
        for i in range(ntries):
            ok = ConfigureFIUOnce.execute({'mode': dest,
                                           'wait': args.get('wait', True)})
            if ok is False:
                log.warning(f'FIU move failed on attempt {i+1} of {ntries}')
                shim_time = cfg.getfloat('times', 'fiu_mode_shim_time', fallback=2)
                time.sleep(shim_time)
            else:
                break
#             try:
#                 ConfigureFIUOnce.execute({'mode': dest,
#                                           'wait': args.get('wait', True)})
#             except KPFQuietException:
#                 log.warning(f'FIU move failed on attempt {i+1} of {ntries}')
#                 shim_time = cfg.getfloat('times', 'fiu_mode_shim_time', fallback=2)
#                 time.sleep(shim_time)
#             else:
#                 break

    @classmethod
    def post_condition(cls, args, logger, cfg):
        if args.get('wait', True) is True:
            dest = args.get('mode')
            kpffiu = ktl.cache('kpffiu')
            modes = kpffiu['MODE'].read()
            if dest.lower() not in modes.lower().split(','):
                raise FailedToReachDestination(dest, modes)
            else:
                log.info(f"FIU mode is now {dest}")

    @classmethod
    def add_cmdline_args(cls, parser, cfg=None):
        '''The arguments to add to the command line interface.
        '''
        parser.add_argument('mode', type=str,
                            choices=['Stowed', 'Alignment', 'Acquisition',
                                     'Observing', 'Calibration'],
                            help='Desired mode (see kpffiu.MODE)')
        parser.add_argument("--nowait", dest="wait",
                            default=True, action="store_false",
                            help="Send move and return immediately?")
        return super().add_cmdline_args(parser, cfg)
