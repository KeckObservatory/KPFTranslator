import time

import ktl

from kpf.KPFTranslatorFunction import KPFTranslatorFunction
from kpf import (log, KPFException, FailedPreCondition, FailedPostCondition,
                 FailedToReachDestination, check_input)


##-------------------------------------------------------------------------
## ZeroOutSlewCalTime
##-------------------------------------------------------------------------
class ZeroOutSlewCalTime(KPFTranslatorFunction):
    '''Zero out the slew cal timer by setting it to the current timestamp.

    ### ARGS
    None
    '''
    @classmethod
    def pre_condition(cls, args, logger, cfg):
        pass

    @classmethod
    def perform(cls, args, logger, cfg):
        log.debug('Updating LASTSLEWCAL time stamp to reset slew cal timer')
        ktl.write('kpfconfig','LASTSLEWCAL', time.time(), binary=True)

    @classmethod
    def post_condition(cls, args, logger, cfg):
        pass
