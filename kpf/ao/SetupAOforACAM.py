import ktl

from kpf.KPFTranslatorFunction import KPFTranslatorFunction
from .. import (log, KPFException, FailedPreCondition, FailedPostCondition,
                FailedToReachDestination, check_input)
from .SetAORotatorManual import SetAORotatorManual
from .SetAORotator import SetAORotator
from .TurnHepaOff import TurnHepaOff
from .SetAODCStoSIM import SetAODCStoSIM
from .ControlAOHatch import ControlAOHatch
from .SetAFMtoMirror import SetAFMtoMirror
from .SendPCUtoHome import SendPCUtoHome
from .SendPCUtoKPF import SendPCUtoKPF
from .SetAFStoNGS import SetAFStoNGS
from .TurnLightSourceOff import TurnLightSourceOff


class SetupAOforACAM(KPFTranslatorFunction):
    '''Set up AO in the safe mode for ACAM operation to assist KPF acquisition
        1. Set AFM to Mirror
        2. Set AFS to ngs
    
    ARGS: None
    '''
    @classmethod
    def pre_condition(cls, args, logger, cfg):
        return True

    @classmethod
    def perform(cls, args, logger, cfg):
        log.info('Set AFM to Mirror')
        SetAFMtoMirror.execute({})

        log.info('Set AFS to NGS')
        SetAFStoNGS.execute({})

    @classmethod
    def post_condition(cls, args, logger, cfg):
        return True