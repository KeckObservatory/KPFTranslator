import ktl

from ddoitranslatormodule.KPFTranslatorFunction import KPFTranslatorFunction
from .. import log
from .SetAORotatorManual import SetAORotatorManual
from .SetAORotator import SetAORotator
from .TurnHepaOff import TurnHepaOff
from .SetAODCStoSIM import SetAODCStoSIM
from .ControlAOHatch import ControlAOHatch
from .SetAFMtoMirror import SetAFMtoMirror
from .SendPCUtoHome import SendPCUtoHome
from .SendPCUtoKPF import SendPCUtoKPF
from .SetAFStoNGS import SetAFStoNGS


class SetupAOforKPF(KPFTranslatorFunction):
    '''Set up AO in the safe mode for KPF operation
        1. Set AO roator in Manual mode
        2. Set AO rotator to 0 deg
        3. Turn off HEPA
        4. Set AO in DCS sim mode
        5. Set AFm to Mirror
        6. Set AFS to ngs
        7. Home PCU <-- to be implemented and tested
        8. Move PCU to the KPF position <-- to be implemented and tested
        9. Open AO hatch 
    '''
    @classmethod
    def pre_condition(cls, args, logger, cfg):
        return True

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

        log.info('Set AFM to Mirror')
        SetAFMtoMirror.execute({})

        log.info('Set AFS to NGS')
        SetAFStoNGS.execute({})

        log.info('Move PCU to Home')
        SendPCUtoHome.execute({})

        log.info('Move PCU to KPF')
        SendPCUtoKPF.execute({})

        log.info('Open AO hatch')
        ControlAOHatch.execute({'destination': 'open'})

    @classmethod
    def post_condition(cls, args, logger, cfg):
        return True