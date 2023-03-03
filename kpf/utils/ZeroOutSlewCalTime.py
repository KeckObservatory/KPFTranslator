import time

import ktl

from ddoitranslatormodule.KPFTranslatorFunction import KPFTranslatorFunction
from .. import (log, KPFException, FailedPreCondition, FailedPostCondition,
                FailedToReachDestination, check_input)


##-------------------------------------------------------------------------
## ZeroOutSlewCalTime
##-------------------------------------------------------------------------
class ZeroOutSlewCalTime(KPFTranslatorFunction):
    '''
    '''
    @classmethod
    def pre_condition(cls, args, logger, cfg):
        return True

    @classmethod
    def perform(cls, args, logger, cfg):
        log.debug('Updating LASTSLEWCAL time stamp to reset slew cal timer')
        ktl.write('kpfconfig','LASTSLEWCAL', time.time(), binary=True)

    @classmethod
    def post_condition(cls, args, logger, cfg):
        return True
