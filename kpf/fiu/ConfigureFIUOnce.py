import time
import ktl

from kpf.KPFTranslatorFunction import KPFTranslatorFunction
from kpf import (log, KPFException, FailedPreCondition, FailedPostCondition,
                 FailedToReachDestination, check_input)


##-----------------------------------------------------------------------------
## Configure FIU Once
##-----------------------------------------------------------------------------
class ConfigureFIUOnce(KPFTranslatorFunction):
    '''Set the FIU mode (kpffiu.MODE) with a single attempt.
    
    This is intended to be wrapped by :py:func:`ConfigureFIU` to handle retries.
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
        fiumode = ktl.cache('kpffiu', 'MODE')
        log.debug(f"Setting FIU mode to {dest}")
        fiumode.write(dest, wait=args.get('wait', True))
        shim_time = cfg.getfloat('times', 'fiu_mode_shim_time', fallback=1)
        time.sleep(shim_time)

    @classmethod
    def post_condition(cls, args, logger, cfg):
        pass
