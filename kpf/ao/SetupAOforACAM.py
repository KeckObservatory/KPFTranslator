import ktl

from kpf.KPFTranslatorFunction import KPFTranslatorFunction
from kpf import (log, KPFException, FailedPreCondition, FailedPostCondition,
                 FailedToReachDestination, check_input)
from kpf.ao.SetAORotatorManual import SetAORotatorManual
from kpf.ao.SetAORotator import SetAORotator
from kpf.ao.TurnHepaOff import TurnHepaOff
from kpf.ao.SetAODCStoSIM import SetAODCStoSIM
from kpf.ao.ControlAOHatch import ControlAOHatch
from kpf.ao.SetAFMtoMirror import SetAFMtoMirror
from kpf.ao.SendPCUtoHome import SendPCUtoHome
from kpf.ao.SendPCUtoKPF import SendPCUtoKPF
from kpf.ao.SetAFStoNGS import SetAFStoNGS
from kpf.ao.TurnLightSourceOff import TurnLightSourceOff


class SetupAOforACAM(KPFTranslatorFunction):
    '''Set up AO in the safe mode for ACAM operation to assist KPF acquisition
        1. Set AFM to Mirror
        2. Set AFS to ngs
    
    ARGS:
    =====
    None
    '''
    @classmethod
    def pre_condition(cls, args, logger, cfg):
        pass

    @classmethod
    def perform(cls, args, logger, cfg):
        log.info('Set AFM to Mirror')
        SetAFMtoMirror.execute({})

        log.info('Set AFS to NGS')
        SetAFStoNGS.execute({})

    @classmethod
    def post_condition(cls, args, logger, cfg):
        pass