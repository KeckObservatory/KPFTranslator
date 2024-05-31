import ktl

from kpf.KPFTranslatorFunction import KPFTranslatorFunction
from kpf import (log, KPFException, FailedPreCondition, FailedPostCondition,
                 FailedToReachDestination, check_input)
from kpf.ao.SetAORotatorManual import SetAORotatorManual
from kpf.ao.SetAORotator import SetAORotator
from kpf.ao.TurnHepaOff import TurnHepaOff
from kpf.ao.SetAODCStoSIM import SetAODCStoSIM
from kpf.ao.SetAFMtoMirror import SetAFMtoMirror
from kpf.ao.SendPCUtoHome import SendPCUtoHome
from kpf.ao.SendPCUtoKPF import SendPCUtoKPF
from kpf.ao.SetAFStoNGS import SetAFStoNGS
from kpf.ao.TurnLightSourceOff import TurnLightSourceOff


class SetupAOforKPF(KPFTranslatorFunction):
    '''# Description
    Set up AO in the safe mode for KPF operation
        1. Set AO roator in Manual mode
        2. Set AO rotator to 0 deg
        3. Turn off HEPA
        4. Set AO in DCS sim mode
        5. Home PCU
        6. Move PCU to the KPF position
        7. Open AO hatch 
    
    # Parameters
    None
    '''
    @classmethod
    def pre_condition(cls, args, logger, cfg):
        pass

    @classmethod
    def perform(cls, args, logger, cfg):
        log.info('Set AO rotator to Manual')
        SetAORotatorManual.execute({})

        log.info('Set AO rotator to 0 deg')
        SetAORotator.execute({'dest': 0})

        log.info('Turn off HEPA')
        TurnHepaOff.execute({})

        log.info('Set AO in DCS sim mode')
        SetAODCStoSIM.execute({})

        log.info('Turn K1 AO light source off')
        TurnLightSourceOff.execute({})

        PCSstagekw = ktl.cache('ao', 'PCSFNAME')
        if PCSstagekw.read() != 'kpf':
            log.info('Move PCU to Home')
            SendPCUtoHome.execute({})
            log.info('Move PCU to KPF')
            SendPCUtoKPF.execute({})

    @classmethod
    def post_condition(cls, args, logger, cfg):
        pass
