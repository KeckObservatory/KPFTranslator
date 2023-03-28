from pathlib import Path

import ktl

from ddoitranslatormodule.KPFTranslatorFunction import KPFTranslatorFunction

from kpf import (log, KPFException, FailedPreCondition, FailedPostCondition,
                 FailedToReachDestination, check_input)
from kpf.scripts import (register_script, obey_scriptrun, check_scriptstop,
                         add_script_log)
from kpf.ao.ControlAOHatch import ControlAOHatch
from kpf.ao.TurnHepaOn import TurnHepaOn
from kpf.ao.SendPCUtoHome import SendPCUtoHome
from kpf.fiu.ShutdownTipTilt import ShutdownTipTilt
from kpf.fiu.ConfigureFIU import ConfigureFIU
from kpf.fiu.WaitForConfigureFIU import WaitForConfigureFIU
from kpf.spectrograph.WaitForReady import WaitForReady
from kpf.spectrograph.SetProgram import SetProgram
from kpf.spectrograph.SetObserver import SetObserver
from kpf.spectrograph.SetObject import SetObject
from kpf.spectrograph.StopAgitator import StopAgitator
from kpf.calbench.CalLampPower import CalLampPower
from kpf.fvc.FVCPower import FVCPower
from kpf.fiu.StopTipTilt import StopTipTilt


class EndOfNight(KPFTranslatorFunction):
    '''Send KPF in to an end of night configuration.

    - kpffiu.MODE = Stowed
    - Power off FVCs
    - Power off LED back illuminators
    - close AO hatch
    - HEPA on
    - Send PCU to Home

    ARGS:
    =====
    :AO: (bool) Close AO hatch, home PCU, and turn on HEPA? (default=True)
    '''
    @classmethod
    @obey_scriptrun
    def pre_condition(cls, args, logger, cfg):
        return True

    @classmethod
    @add_script_log(Path(__file__).name.replace(".py", ""))
    def perform(cls, args, logger, cfg):
        StopTipTilt.execute({})

        # Start FIU stow
        log.info('Setting FIU mode to Stowed')
        ConfigureFIU.execute({'mode': 'Stowed', 'wait': False})

        if args.get('AO', True) is True:

            # ---------------------------------
            # User Verification
            # ---------------------------------
            msg = ["",
                   "--------------------------------------------------------------",
                   "This script will configure the FIU and AO bench.",
                   "The AO bench area should be clear of personnel before proceeding.",
                   "Do you wish to to continue? [Y/n]",
                   "--------------------------------------------------------------",
                   "",
                   ]
            for line in msg:
                print(line)
            user_input = input()
            if user_input.lower() in ['n', 'no', 'q', 'quit', 'abort']:
                log.warning(f'User aborted Start Of Night')
                return

            log.info('Closing AO Hatch')
            ControlAOHatch.execute({'destination': 'closed'})
#             log.info('Turning on AO HEPA Filter System')
#             TurnHepaOn.execute({})
            log.info('Sending PCU stage to Home position')
            SendPCUtoHome.execute({})
        # Power off FVCs
        for camera in ['SCI', 'CAHK', 'CAL']:
            FVCPower.execute({'camera': camera, 'power': 'off'})
        # Power off FVCs
        for LED in ['ExpMeterLED', 'CaHKLED', 'SciLED', 'SkyLED']:
            CalLampPower.execute({'lamp': LED, 'power': 'off'})
        # Finish FIU shutdown
        StopAgitator.execute({})
        WaitForConfigureFIU.execute({'mode': 'Stowed'})
        # Set PROGNAME
        log.info('Clearing values for PROGNAME, OBSERVER, OBJECT')
        WaitForReady.execute({})
        SetProgram.execute({'progname': ''})
        SetObserver.execute({'observer': ''})
        SetObject.execute({'Object': ''})
        # Allow scheduledm cals
        log.info('Set ALLOWSCHEDULEDCALS to Yes')
        kpfconfig = ktl.cache('kpfconfig')
        kpfconfig['ALLOWSCHEDULEDCALS'].write('Yes')

    @classmethod
    def post_condition(cls, args, logger, cfg):
        return True

    @classmethod
    def add_cmdline_args(cls, parser, cfg=None):
        '''The arguments to add to the command line interface.
        '''
        parser = cls._add_bool_arg(parser, 'AO',
            'Close AO hatch, send PCU home, and turn on HEPA filter?', default=True)
        return super().add_cmdline_args(parser, cfg)
