import ktl

from ddoitranslatormodule.KPFTranslatorFunction import KPFTranslatorFunction

from .. import log
from ..ao.ControlAOHatch import ControlAOHatch
from ..ao.TurnHepaOn import TurnHepaOn
from ..ao.SendPCUtoHome import SendPCUtoHome
from ..fiu.ShutdownTipTilt import ShutdownTipTilt
from ..fiu.ConfigureFIU import ConfigureFIU
from ..fiu.WaitForConfigureFIU import WaitForConfigureFIU
from ..spectrograph.WaitForReady import WaitForReady
from ..spectrograph.SetProgram import SetProgram
from ..spectrograph.SetObserver import SetObserver
from ..spectrograph.SetObject import SetObject
from ..calbench.CalLampPower import CalLampPower
from ..fvc.FVCPower import FVCPower


class EndOfNight(KPFTranslatorFunction):
    '''Send KPF in to an end of night configuration.

    - kpffiu.MODE = Stowed
    - Power off FVCs
    - Power off LED back illuminators
    - close AO hatch
    - HEPA on
    - Send PCU to Home
    
    ARGS:
    AO (bool) - Close AO hatch, home PCU, and turn on HEPA? (default=True)
    '''
    @classmethod
    def pre_condition(cls, args, logger, cfg):
        return True

    @classmethod
    def perform(cls, args, logger, cfg):
        # Start FIU stow

        if args.get('cals', True) is True:
            log.info('Setting FIU mode to Calibration')
            ConfigureFIU.execute({'mode': 'Calibration', 'wait': False})
        else:
            log.info('Setting FIU mode to Stowed')
            ConfigureFIU.execute({'mode': 'Stowed', 'wait': False})

        if args.get('AO', True) is True:
            log.info('Closing AO Hatch')
            ControlAOHatch.execute({'destination': 'closed'})
            log.info('Turning on AO HEPA Filter System')
            TurnHepaOn.execute({})
            log.info('Sending PCU stage to Home position')
            SendPCUtoHome.execute({})
        # Finish FIU shutdown
        if args.get('cals', True) is True:
            WaitForConfigureFIU.execute({'mode': 'Calibration'})
        else:
            WaitForConfigureFIU.execute({'mode': 'Stowed'})
        ShutdownTipTilt.execute({})
        # Power off FVCs
        for camera in ['SCI', 'CAHK', 'CAL']:
            FVCPower.execute({'camera': camera, 'power': 'off'})
        # Power off FVCs
        for LED in ['ExpMeterLED', 'CaHKLED', 'SciLED', 'SkyLED']:
            CalLampPower.execute({'lamp': LED, 'power': 'off'})
        # Set PROGNAME
        log.info('Clearing values for PROGNAME, OBSERVER, OBJECT')
        WaitForReady.execute({})
        SetProgram.execute({'progname': ''})
        SetObserver.execute({'observer': ''})
        SetObject.execute({'Object': ''})
        log.info('Set SCRIPTALLOW to Yes')
        scriptallow = ktl.cache('kpfconfig', 'SCRIPTALLOW')
        scriptallow.write('Yes')

    @classmethod
    def post_condition(cls, args, logger, cfg):
        return True

    @classmethod
    def add_cmdline_args(cls, parser, cfg=None):
        '''The arguments to add to the command line interface.
        '''
        parser = cls._add_bool_arg(parser, 'AO',
            'Close AO hatch, send PCU home, and turn on HEPA filter?', default=True)
        parser = cls._add_bool_arg(parser, 'cals',
            'Set FIU to calibration mode instead of stowed?', default=True)

        return super().add_cmdline_args(parser, cfg)
