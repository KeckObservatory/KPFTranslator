from collections import OrderedDict

import ktl

from ddoitranslatormodule.KPFTranslatorFunction import KPFTranslatorFunction

from ..ao.CloseAOHatch import CloseAOHatch
from ..ao.TurnHepaOn import TurnHepaOn


class EndOfNight(KPFTranslatorFunction):
    '''Send KPF in to an end of night configuration.

    - kpffiu.MODE = Stowed
    - kpfguide.SENSORSETP = 0
    - Power off LED back illuminators
    - Power off FVCs
    - Power off Calibration lamps

    - close AO hatch
    - HEPA on
    '''
    @classmethod
    def pre_condition(cls, args, logger, cfg):
        return True

    @classmethod
    def perform(cls, args, logger, cfg):
        # FIU
        print('Setting FIU mode to Stowed')
        kpffiu = ktl.cache('kpffiu')
        kpffiu['MODE'].write('Stowed')
        # Guider
        print('Setting guider set point to 0C')
        kpfguide = ktl.cache('kpfguide')
        kpfguide['SENSORSETP'].write(0)
        # Power off Back Illuminators, FVCs, Lamps
        kpfpower = ktl.cache('kpfpower')
        outlets = ['E7', 'E8', 'H1', 'J7', 'K5', 'K6', 'F6', 'L1', 'L2', 'G5',
                   'G6', 'G7', 'G8']
        for outlet in outlets:
            name = kpfpower[f'OUTLET_{outlet}_NAME'].read()
            locked = (kpfpower[f'OUTLET_{outlet}_LOCK'].read() == 'Locked')
            if locked is True:
                print(f'{outlet} ({name}) is Locked')
            else:
                print(f'Powering off {outlet}: {name}')
                kpfpower[f'OUTLET_{outlet}'].write('Off')
        # Close AO Hatch
        CloseAOHatch.execute({})
        # Turn HELP Filter On
        TurnHepaOn.execute({})


    @classmethod
    def post_condition(cls, args, logger, cfg):
        return True
