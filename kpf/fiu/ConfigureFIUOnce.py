import time
import ktl

from kpf import log, cfg
from kpf.exceptions import *
from kpf.KPFTranslatorFunction import KPFFunction, KPFScript


##-----------------------------------------------------------------------------
## Configure FIU Once
##-----------------------------------------------------------------------------
class ConfigureFIUOnce(KPFFunction):
    '''Set the FIU mode (kpffiu.MODE) with a single attempt. This is intended
    to be wrapped by `ConfigureFIU` to handle retries.

    Args:
        mode (str): The desired FIU mode. Allowed values: Stowed, Alignment,
            Acquisition, Observing, Calibration
        wait (bool): Wait for move to complete before returning? (default: True)

    KTL Keywords Used:

    - `kpffiu.MODE`
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
        log.debug(f"Setting FIU mode to {dest}")
        fiumode.write(dest, wait=args.get('wait', True))
        shim_time = cfg.getfloat('times', 'fiu_mode_shim_time', fallback=1)
        time.sleep(shim_time)

    @classmethod
    def post_condition(cls, args):
        pass
