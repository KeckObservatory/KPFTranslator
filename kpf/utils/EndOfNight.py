from pathlib import Path
import os

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

    Args:
        AO (bool): Close AO hatch, home PCU, and turn on HEPA? (default=True)

    KTL Keywords Used:

    - `kpfexpose.EXPOSE`
    - `kpfconfig.SCRIPTNAME`
    - `kpfconfig.SCRIPTPID`
    - `kpfconfig.SCRIPTSTOP`
    - `kpfconfig.SIMULCALSOURCE`
    - `kpfconfig.ALLOWSCHEDULEDCALS`

    Functions Called:

    - `kpf.ao.ControlAOHatch`
    - `kpf.ao.TurnHepaOn`
    - `kpf.ao.SendPCUtoHome`
    - `kpf.fiu.ShutdownTipTilt`
    - `kpf.fiu.ConfigureFIU`
    - `kpf.fiu.WaitForConfigureFIU`
    - `kpf.spectrograph.WaitForReady`
    - `kpf.spectrograph.SetProgram`
    - `kpf.spectrograph.SetObserver`
    - `kpf.spectrograph.SetObject`
    - `kpf.spectrograph.StopAgitator`
    - `kpf.calbench.CalLampPower`
    - `kpf.fvc.FVCPower`
    - `kpf.fiu.StopTipTilt`
    '''
    @classmethod
    @obey_scriptrun
    def pre_condition(cls, args):
        pass

    @classmethod
    @add_script_log(Path(__file__).name.replace(".py", ""))
    def perform(cls, args):
        # Check Scripts
        kpfconfig = ktl.cache('kpfconfig')
        expose = ktl.cache('kpfexpose', 'EXPOSE')
        scriptname = kpfconfig['SCRIPTNAME'].read()
        pid = kpfconfig['SCRIPTPID'].read(binary=True)
        script_running = scriptname not in ['', 'None', None] or pid >= 0
        if script_running and args.get('confirm', False) is True:
            log.error('Non-interactive mode set and script is running')
            return
        if script_running:
            # ---------------------------------
            # User Verification
            # ---------------------------------
            msg = ["",
                   "--------------------------------------------------------------",
                   f"A script ({scriptname}, {pid}) is currently running. ",
                   "",
                   "Do you wish to end the current exposure and request a script",
                   "stop in order to proceed with running EndOfNight?",
                   "",
                   "End Exposure and Request Script Stop?",
                   "(y/n) [y]:",
                   "--------------------------------------------------------------",
                   "",
                   ]
            for line in msg:
                print(line)
            user_input = input()
            if user_input.lower() in ['n', 'no', 'q', 'quit', 'abort']:
                log.warning(f'User aborted End Of Night')
                return
            else:
                log.info('User opted to stop existing script')
                kpfconfig['SCRIPTSTOP'].write(1)
                expose.write('End')
                waittime = 120
                log.info(f'Waiting up to {waittime:.0f}s for running script to end')
                kpfconfig['SCRIPTPID'].waitFor("==-1", timeout=waittime)
                time.sleep(2) # time shim
                check_script_running()

        # Stop tip tilt and agitator
        StopTipTilt.execute({})
        StopAgitator.execute({})

        # Start FIU stow
        log.info('Setting FIU mode to Stowed')
        ConfigureFIU.execute({'mode': 'Stowed', 'wait': False})

        # ---------------------------------
        # AO Shutdown
        # ---------------------------------
        if args.get('AO', True) is True and args.get('confirm', False) is False:
            msg = ["",
                   "--------------------------------------------------------------",
                   "Perform shutdown of AO? This will:",
                   "  - Close the AO hatch",
                   "  - Send the PCU to home",
                   "These steps should not be run if OSIRIS is in use.",
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
                except Exception as e:
                    log.error(f"Failure controlling AO hatch")
                    log.error(e)
                log.info('Sending PCU stage to Home position')
                try:
                    SendPCUtoHome.execute({})
                except Exception as e:
                    log.error(f"Failure sending PCU to home")
                    log.error(e)
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
        calsource = kpfconfig['SIMULCALSOURCE'].read()
        if calsource in ['U_gold', 'U_daily', 'Th_daily', 'Th_gold']:
            CalLampPower.execute({'lamp': calsource, 'power': 'off'})
        # Allow scheduled cals
        log.info('Set ALLOWSCHEDULEDCALS to Yes')
        kpfconfig['ALLOWSCHEDULEDCALS'].write('Yes')

    @classmethod
    def post_condition(cls, args):
        pass

    @classmethod
    def add_cmdline_args(cls, parser):
        parser.add_argument("--noAO", dest="AO",
                            default=True, action="store_false",
                            help="Skip configuring AO?")
        parser.add_argument("--confirm", dest="confirm",
                            default=False, action="store_true",
                            help="Skip confirmation questions (script will be non interactive)?")
        return super().add_cmdline_args(parser)
