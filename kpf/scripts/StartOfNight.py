from collections import OrderedDict

import ktl

from ddoitranslatormodule.KPFTranslatorFunction import KPFTranslatorFunction

from ..ao.SetupAOforKPF import SetupAOforKPF
from ..fiu.InitializeTipTilt import InitializeTipTilt
from ..fiu.ConfigureFIU import ConfigureFIU
from .SetOutdirs import SetOutdirs


class StartOfNight(KPFTranslatorFunction):
    '''Send KPF in to a reasonable starting configuration
    
    - kpfguide.SENSORSETP = -40
    - initialize tip tilt (set closed loop mode and 0, 0)
    - set FIU mode to observing
    - Seup AO
    - Set OUTDIRS
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
        print('Configure FIU for "Observing"')
        ConfigureFIU({'mode': 'Observing'})
        print('Initialize tip tilt mirror')
        InitializeTipTilt.execute({})
        # Set Outdirs
        SetOutdirs.execute({})

        if args.get('AO', True) is True:
            SetupAOforKPF.execute({})

    @classmethod
    def post_condition(cls, args, logger, cfg):
        return True

    @classmethod
    def add_cmdline_args(cls, parser, cfg=None):
        parser = cls._add_bool_arg(parser, 'AO',
            'Configure AO?', default=True)

        return super().add_cmdline_args(parser, cfg)
