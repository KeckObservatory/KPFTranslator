from pathlib import Path

import ktl

from kpf import log, cfg
from kpf.exceptions import *
from kpf.KPFTranslatorFunction import KPFFunction, KPFScript
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


class EndOfNight(KPFFunction):
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
    def pre_condition(cls, args):
        pass

    @classmethod
    @register_script(Path(__file__).name, os.getpid())
    @add_script_log(Path(__file__).name.replace(".py", ""))
    def perform(cls, args):
        StopTipTilt.execute({})
        StopAgitator.execute({})

        # Start FIU stow
        log.info('Setting FIU mode to Stowed')
        ConfigureFIU.execute({'mode': 'Stowed', 'wait': False})

        # ---------------------------------
        # User Verification for AO Shutdown
        # ---------------------------------
        msg = ["",
               "--------------------------------------------------------------",
               "Perform shutdown of AO? This will move the AO hatch and PCU.",
               "The AO area should be clear of personnel before proceeding.",
               "",
               "Do you wish to shutdown AO?",
               "(y/n) [y]:",
               "--------------------------------------------------------------",
               "",
               ]
        for line in msg:
            print(line)
        user_input = input()
        if user_input.lower() in ['y', 'yes', '']:
            log.debug('User chose to shut down AO')
            log.info('Closing AO Hatch')
            try:
                ControlAOHatch.execute({'destination': 'closed'})
            except FailedToReachDestination:
                log.error(f"AO hatch did not move successfully")
            log.info('Sending PCU stage to Home position')
            SendPCUtoHome.execute({})
#             log.info('Turning on AO HEPA Filter System')
#             TurnHepaOn.execute({})
        else:
            log.warning(f'User chose to skip AO shutdown')

        # ---------------------------------
        # Remaining non-AO Actions
        # ---------------------------------
        # Power off FVCs
        for camera in ['SCI', 'CAHK', 'CAL']:
            FVCPower.execute({'camera': camera, 'power': 'off'})
        # Power off LEDs
        for LED in ['ExpMeterLED', 'CaHKLED', 'SciLED', 'SkyLED']:
            CalLampPower.execute({'lamp': LED, 'power': 'off'})
        # Finish FIU shutdown
        WaitForConfigureFIU.execute({'mode': 'Stowed'})
        # Set PROGNAME
        log.info('Clearing values for PROGNAME, OBSERVER, OBJECT')
        WaitForReady.execute({})
        SetProgram.execute({'progname': ''})
        SetObserver.execute({'observer': ''})
        SetObject.execute({'Object': ''})
        # Power off Simulcal lamp
        kpfconfig = ktl.cache('kpfconfig')
        calsource = kpfconfig['SIMULCALSOURCE'].read()
        if calsource in ['U_gold', 'U_daily', 'Th_daily', 'Th_gold']:
            CalLampPower.execute({'lamp': calsource, 'power': 'off'})
        # Allow scheduled cals
        log.info('Set ALLOWSCHEDULEDCALS to Yes')
        kpfconfig = ktl.cache('kpfconfig')
        kpfconfig['ALLOWSCHEDULEDCALS'].write('Yes')

    @classmethod
    def post_condition(cls, args):
        pass
