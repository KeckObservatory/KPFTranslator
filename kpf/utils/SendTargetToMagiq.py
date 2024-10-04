import ktl

from kpf.KPFTranslatorFunction import KPFTranslatorFunction
from kpf import (log, KPFException, FailedPreCondition, FailedPostCondition,
                 FailedToReachDestination, check_input)


##-------------------------------------------------------------------------
## SendTargetToMagiq
##-------------------------------------------------------------------------
class SendTargetToMagiq(KPFTranslatorFunction):
    '''
    '''
    @classmethod
    def pre_condition(cls, target):
        pass

    @classmethod
    def perform(cls, target):
        pass

    @classmethod
    def post_condition(cls, target):
        pass
