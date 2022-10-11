from collections import OrderedDict

import ktl

from ddoitranslatormodule.KPFTranslatorFunction import KPFTranslatorFunction

from ..ao.OpenAOHatch import OpenAOHatch
from ..ao.TurnHepaOff import TurnHepaOff
from ..ao.SetPCUtoKPF import SetPCUtoKPF


class StartOfNight(KPFTranslatorFunction):
    '''Send KPF in to a reasonable starting configuration
    
    - kpfguide.SENSORSETP = -40
    
    - PCU stage to KPF position
    - open AO hatch
    - HEPA Off
    '''
    @classmethod
    def pre_condition(cls, args, logger, cfg):
        return True

    @classmethod
    def perform(cls, args, logger, cfg):
        # Guider
        print('Setting guider set point to -40 C')
        kpfguide = ktl.cache('kpfguide')
        kpfguide['SENSORSETP'].write(-40)
        # Open AO Hatch
        OpenAOHatch.execute({})
        # Turn HELP Filter On
        TurnHepaOff.execute({})
        # Set PCU Stage to KPF Position
        SetPCUtoKPF.execute({})


    @classmethod
    def post_condition(cls, args, logger, cfg):
        return True
