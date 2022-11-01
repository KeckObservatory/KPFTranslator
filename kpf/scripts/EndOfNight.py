import ktl

from ddoitranslatormodule.KPFTranslatorFunction import KPFTranslatorFunction

from .. import log
from ..ao.CloseAOHatch import CloseAOHatch
from ..ao.TurnHepaOn import TurnHepaOn
from ..fiu.ShutdownTipTilt import ShutdownTipTilt
from ..fiu.ConfigureFIU import ConfigureFIU


class EndOfNight(KPFTranslatorFunction):
    '''Send KPF in to an end of night configuration.

    - kpffiu.MODE = Stowed
    - Tip tilt mirror in open loop mode
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
        log.info('Setting FIU mode to Stowed')
        ConfigureFIU.execute({'mode': 'Stowed'})
        ShutdownTipTilt.execute({})
        # Guider
        log.info('Setting guider set point to 0C')
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
                log.info(f'{outlet} ({name}) is Locked')
            else:
                log.info(f'Powering off {outlet}: {name}')
                kpfpower[f'OUTLET_{outlet}'].write('Off')

        if args.get('AO', True) is True:
            ControlAOHatch.execute({'destination': 'close'})
            TurnHepaOn.execute({})


    @classmethod
    def post_condition(cls, args, logger, cfg):
        return True

    @classmethod
    def add_cmdline_args(cls, parser, cfg=None):
        '''The arguments to add to the command line interface.
        '''
        parser = cls._add_bool_arg(parser, 'AO',
            'Close AO hatch and turn on HEPA filter?', default=True)

        return super().add_cmdline_args(parser, cfg)
