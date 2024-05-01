import ktl

from kpf.KPFTranslatorFunction import KPFTranslatorFunction
from kpf import (log, KPFException, FailedPreCondition, FailedPostCondition,
                 FailedToReachDestination, check_input)


class IsSoCalOnTarget(KPFTranslatorFunction):
    '''Return a boolean indicating whether SoCal in on target and ready to take
    data.

    ARGS:
    =====
    None
    '''
    @classmethod
    def pre_condition(cls, args, logger, cfg):
        pass

    @classmethod
    def perform(cls, args, logger, cfg):
        socal = ktl.cache('kpfsocal')
        # Check if enclosure is open
        #   * kpfsocal.ENCSTA = 0
        # Check if EKO is tracking:
        #   * kpfsocal.EKOONLINE = Online
        #   * kpfsocal.EKOMODE = 3
        # Check Pyrheliometer flux?
        #   * kpfsocal.PYRIRRAD > ??
        # Check operations loop
        #   * kpfsocal.AUTONOMOUS = 1
        #   * kpfsocal.CAN_OPEN = True
        #   * kpfsocal.IS_OPEN = True
        #   * kpfsocal.IS_TRACKING = True
        #   * kpfsocal.ONLINE = True
        #   * kpfsocal.STATE = ?

    @classmethod
    def post_condition(cls, args, logger, cfg):
        pass
