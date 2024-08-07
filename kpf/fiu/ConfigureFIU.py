import time
import ktl

from kpf.KPFTranslatorFunction import KPFTranslatorFunction
from kpf import (log, KPFException, FailedPreCondition, FailedPostCondition,
                 FailedToReachDestination, check_input)
from kpf.fiu.ConfigureFIUOnce import ConfigureFIUOnce
from kpf.fiu.WaitForConfigureFIU import WaitForConfigureFIU


##-----------------------------------------------------------------------------
## Configure FIU
##-----------------------------------------------------------------------------
class ConfigureFIU(KPFTranslatorFunction):
    '''Set the FIU mode (kpffiu.MODE). If the wait option is fale this will
    retry the move if it fails with a configurable number of retries.

    Args:
        mode (str): The desired FIU mode. Allowed values: Stowed, Alignment,
            Acquisition, Observing, Calibration
        wait (bool): Wait for move to complete before returning? (default: True)

    KTL Keywords Used:

    - `kpffiu.MODE`

    Scripts Called:

    - `kpf.calbench.ConfigureFIUOnce`
    - `kpf.calbench.WaitForConfigureFIU`
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
        wait = args.get('wait', True)
        log.info(f"Configuring FIU for {dest}")
        ConfigureFIUOnce.execute({'mode': dest, 'wait': wait})
        if wait == True:
            WaitForConfigureFIU.execute({'mode': dest})

    @classmethod
    def post_condition(cls, args, logger, cfg):
        pass

    @classmethod
    def add_cmdline_args(cls, parser, cfg=None):
        parser.add_argument('mode', type=str,
                            choices=['Stowed', 'Alignment', 'Acquisition',
                                     'Observing', 'Calibration'],
                            help='Desired mode (see kpffiu.MODE)')
        parser.add_argument("--nowait", dest="wait",
                            default=True, action="store_false",
                            help="Send move and return immediately?")
        return super().add_cmdline_args(parser, cfg)
