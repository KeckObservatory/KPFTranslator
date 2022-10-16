import ktl

from ddoitranslatormodule.KPFTranslatorFunction import KPFTranslatorFunction

from .SetAORotatorManual import SetAORotatorManual
from .SetAORotator import SetAORotator
from .TurnHepaOff import TurnHepaOff
from .SetAODCStoSIM import SetAODCStoSIM
from .OpenAOHatch import OpenAOHatch
from .SetAFMtoMirror import SetAFMtoMirror
from .SetPCUtoKPF import SetPCUtoKPF
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
        print('Set AO rotator to Manual')
        SetAORotatorManual.execute({})

        print('Set AO rotator to 0 deg')
        SetAORotator.execute({'dest': 0})

        print('Turn off HEPA')
        TurnHepaOff.execute({})

        print('Set AO in DCS sim mode')
        SetAODCStoSIM.execute({})

        print('Set AFM to Mirror')
        SetAFMtoMirror.execute({})

        print('Set AFS to NGS')
        SetAFStoNGS.execute({})

        print('Move PCU to KPF')
        SetPCUtoKPF.execute({})

        print('Open AO hatch')
        OpenAOHatch.execute({})

    @classmethod
    def post_condition(cls, args, logger, cfg):
        return True