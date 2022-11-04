import ktl

from ddoitranslatormodule.KPFTranslatorFunction import KPFTranslatorFunction

from .. import log
from ..ao.ControlAOHatch import ControlAOHatch
from ..ao.TurnHepaOn import TurnHepaOn
from ..fiu.ShutdownTipTilt import ShutdownTipTilt
from ..fiu.ConfigureFIU import ConfigureFIU
from ..spectrograph.SetProgram import SetProgram
from ..spectrograph.SetObserver import SetObserver
from ..spectrograph.SetObject import SetObject
from ..calbench.CalLampPower import CalLampPower
from ..fvc.FVCPower import FVCPower


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
#         log.info('Setting guider set point to 0C')
#         kpfguide = ktl.cache('kpfguide')
#         kpfguide['SENSORSETP'].write(0)
        # Power off cal lamps and LEDs
        lamps = ['BrdbandFiber', 'U_gold', 'U_daily', 'Th_daily', 'Th_gold',
                 'WideFlat', 'ExpMeterLED', 'CaHKLED', 'SciLED', 'SkyLED']
        for lamp in lamps:
            CalLampPower.execute({'lamp': lamp, 'power': 'off'})
        # Power off FVCs
        for camera in ['SCI', 'CAHK', 'EXT', 'CAL']:
            FVCPower.execute({'camera': camera, 'power': 'off'})
        # Set PROGNAME
        log.info('Clearing values for PROGNAME, OBSERVER, OBJECT')
        SetProgram.execute({'progname': ''})
        SetObserver.execute({'observer': ''})
        SetObject.execute({'Object': ''})

        if args.get('AO', True) is True:
            log.info('Closing AO Hatch')
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
