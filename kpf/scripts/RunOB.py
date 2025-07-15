import sys
import time
import os
import traceback
from pathlib import Path
import yaml

import ktl

from kpf import log, cfg
from kpf.exceptions import *
from kpf.KPFTranslatorFunction import KPFFunction, KPFScript
from kpf.scripts import (check_script_running, set_script_keywords,
                         add_script_log, wait_for_script, clear_script_keywords)
from kpf.ObservingBlocks.ObservingBlock import ObservingBlock
from kpf.fiu.VerifyCurrentBase import VerifyCurrentBase
from kpf.scripts.SetTargetInfo import SetTargetInfo
from kpf.scripts.ConfigureForCalibrations import ConfigureForCalibrations
from kpf.scripts.ExecuteCal import ExecuteCal
from kpf.scripts.CleanupAfterCalibrations import CleanupAfterCalibrations
from kpf.scripts.ConfigureForAcquisition import ConfigureForAcquisition
from kpf.scripts.WaitForConfigureAcquisition import WaitForConfigureAcquisition
from kpf.scripts.ConfigureForScience import ConfigureForScience
from kpf.scripts.WaitForConfigureScience import WaitForConfigureScience
from kpf.scripts.ExecuteSci import ExecuteSci
from kpf.scripts.CleanupAfterScience import CleanupAfterScience
from kpf.spectrograph.SetProgram import SetProgram
from kpf.observatoryAPIs import addObservingBlockHistory


class RunOB(KPFScript):
    '''Script to run an OB.

    ARGS:
    =====
    * __leave_lamps_on__ - `bool` Leave calibration lamps on when done?
    * __OB__ - `ObservingBlock` or `dict` A valid observing block (OB).
    '''
    @classmethod
    def pre_condition(cls, args, OB=None):
        # If specified obey the ALLOWSCHEDULEDCALS keyword
        if args.get('scheduled', False) == True:
            ALLOWSCHEDULEDCALS = ktl.cache('kpfconfig', 'ALLOWSCHEDULEDCALS')
            if ALLOWSCHEDULEDCALS.read(binary=True) == False:
                raise FailedPreCondition('ALLOWSCHEDULEDCALS is No')
        # Validate the OB
        OB.validate()
        # Check for script running unless waitforscript is set
        if args.get('waitforscript', False) is False:
            check_script_running()

    @classmethod
    @add_script_log(Path(__file__).name.replace(".py", ""))
    def perform(cls, args, OB=None):
        # -------------------------------------------------------------
        # If requested wait for an existing script to complete
        # -------------------------------------------------------------
        if args.get('waitforscript', False) == True:
            newscript = f'{Path(__file__).name.replace(".py", "")}(PID {os.getpid()})'
            wait_for_script(newscript=newscript)
        set_script_keywords(Path(__file__).name, os.getpid())

        log.info('-------------------------')
        log.info(f"Running {cls.__name__}")
        log.info('-------------------------')
        if isinstance(OB, dict):
            OB = ObservingBlock(OB)
        if OB.OBID not in [None, '']:
            log.info(f"OB ID = {OB.OBID}")

        # -------------------------------------------------------------
        # Set Target info for OA's Tip Tilt GUI
        # -------------------------------------------------------------
        if OB.Target is not None:
            SetTargetInfo.execute({}, OB=OB)

        # -------------------------------------------------------------
        # Add slew cal to OB if keywords indicate one is requested
        # -------------------------------------------------------------
        SLEWCALREQ = ktl.cache('kpfconfig', 'SLEWCALREQ')
        SLEWCALFILE = ktl.cache('kpfconfig', 'SLEWCALFILE')
        SCRIPTMSG = ktl.cache('kpfconfig', 'SCRIPTMSG')
        if len(OB.Observations) > 0 and SLEWCALREQ.read(binary=True) is True:
            slewcal_OBfile = Path(SLEWCALFILE.read())
            log.info('Slewcal has been requested')
            log.debug(f"Reading: {slewcal_OBfile}")
            with open(slewcal_OBfile, 'r') as file:
                slewcal_OBdict = yaml.safe_load(file)
                slewcal_OB = ObservingBlock(slewcal_OBdict)
            OB.Calibrations.extend(slewcal_OB.Calibrations)
            # Now that slewcal has been added, reset the SLEWCALREQ value
            SLEWCALREQ.write(False)


        if len(OB.Calibrations) > 0:
            # -------------------------------------------------------------
            # Configure for Calibrations
            # -------------------------------------------------------------
            try:
                SCRIPTMSG.write('Configuring for Calibrations')
                ConfigureForCalibrations.execute(args, OB=OB)
            except ScriptStopTriggered as scriptstop:
                log.error('Script Stop Triggered')
                CleanupAfterCalibrations.execute(args, OB=OB)
                clear_script_keywords()
                return
            except Exception as e:
                log.error('Exception encountered during ExecuteSci')
                log.error(e)
                CleanupAfterCalibrations.execute(args, OB=OB)
                clear_script_keywords()
                return

            # -------------------------------------------------------------
            # Loop over calibrations and execute
            # -------------------------------------------------------------
            for i,calibration in enumerate(OB.Calibrations):
                log.info(f'Executing Calibration {i+1}/{len(OB.Calibrations)}')
                try:
                    ExecuteCal.execute(calibration.to_dict())
                except ScriptStopTriggered as scriptstop:
                    log.error('Script Stop Triggered')
                    CleanupAfterCalibrations.execute(args, OB=OB)
                    clear_script_keywords()
                    return
                except Exception as e:
                    log.error('Exception encountered during ExecuteCal')
                    log.error(e)
                    CleanupAfterCalibrations.execute(args, OB=OB)
                    clear_script_keywords()
                    return

            # -------------------------------------------------------------
            # Clean up after calibrations
            # -------------------------------------------------------------
            if len(OB.Observations) > 0:
                # Don't stop FIU if we have observations to perform
                args['FIUdest'] = 'Observing'
                SCRIPTMSG.write('Calibrations complete. Setting FIU to observing mode')
            CleanupAfterCalibrations.execute(args, OB=OB)


        if OB.Target is not None:
            # -------------------------------------------------------------
            # Configure for Acquisition
            # -------------------------------------------------------------
            log.info(f'Configuring for Acquisition')
            try:
                ConfigureForAcquisition.execute(args, OB=OB)
                WaitForConfigureAcquisition.execute(args, OB=OB)
            except ScriptStopTriggered as scriptstop:
                log.error('Script Stop Triggered')
                CleanupAfterScience.execute(args, OB=OB)
                return
            except Exception as e:
                log.error('Exception encountered during ConfigureForAcquisition')
                log.error(e)
                CleanupAfterScience.execute(args, OB=OB)
                return
            # Proceed once target is on fiber and tip tilt is active
            log.debug('Asking for user input')
            print()
            print("###############################################################")
            print("    Before continuing, please ensure that the OA has placed")
            print("    the star on the KPF PO and they have initiated tip tilt")
            print("    corrections (if desired).")
            print()
            print("    Press 'Enter' to begin exposure(s) or 'a' to abort script")
            print("###############################################################")
            print()
            user_input = input()
            log.debug(f'response: "{user_input}"')
            if user_input.lower() in ['a', 'abort', 'q', 'quit']:
                log.error("User chose to halt execution")
                CleanupAfterScience.execute(args, OB=OB)
                clear_script_keywords()
                return
            # Verify dcs TARGNAME against OB.Target.TargetName
            dcsint = cfg.getint('telescope', 'telnr', fallback=1)
            TARGNAME = ktl.cache(f'dcs{dcsint:1d}', 'TARGNAME').read()
            if TARGNAME.strip().lower() != OB.Target.TargetName.lower():
                log.warning('Target name mismatch detected')
                log.warning(f"dcs.TARGNAME '{TARGNAME}' != OB TargetName '{OB.Target.TargetName}'")
                log.debug('Asking for user input')
                print()
                print("###############################################################")
                print("    WARNING: The telescope control system target name: {TARGNAME}")
                print("    WARNING: does not match the OB target name: {OB.Target.TargetName}")
                print()
                print("    Press 'Enter' to begin exposure(s) anyway or 'a' to abort script")
                print("###############################################################")
                print()
                user_input = input()
                log.debug(f'response: "{user_input}"')
                if user_input.lower() in ['a', 'abort', 'q', 'quit']:
                    log.error("User chose to halt execution")
                    CleanupAfterScience.execute(args, OB=OB)
                    clear_script_keywords()
                    return
            # Verify Current Base
            try:
                VerifyCurrentBase.execute({'query_user': True})
            except Exception as e:
                log.error('Exception encountered during VerifyCurrentBase')
                log.error(e)
                CleanupAfterScience.execute(args, OB=OB)
                clear_script_keywords()
                return


        if len(OB.Observations) > 0:
            for i,observation in enumerate(OB.Observations):
                # -------------------------------------------------------------
                # Configure for Science
                # -------------------------------------------------------------
                try:
                    observation_dict = observation.to_dict()
                    observation_dict['Gmag'] = OB.Target.get('Gmag')
                    ConfigureForScience.execute(observation_dict)
                    if OB.ProgramID != '':
                        SetProgram.execute({'progname': OB.ProgramID})
                    WaitForConfigureScience.execute(observation_dict)
                except ScriptStopTriggered as scriptstop:
                    log.error('Script Stop Triggered')
                    CleanupAfterScience.execute(args, OB=OB)
                    clear_script_keywords()
                    return
                except Exception as e:
                    log.error('Exception encountered during ConfigureForScience')
                    log.error(e)
                    CleanupAfterScience.execute(args, OB=OB)
                    clear_script_keywords()
                    return

                # -------------------------------------------------------------
                # Execute Observation
                # -------------------------------------------------------------
                log.info(f'Executing Observation {i+1}/{len(OB.Observations)}')
                try:
                    history, scriptstop = ExecuteSci.execute(observation_dict)
                    log.info(f'History of execution:')
                    log.info(f"  Start Times: {history['exposure_start_times']}")
                    log.info(f"  Exposure Times: {history['exposure_times']}")
                    log.debug(history)
                    if OB.OBID != '':
                        history['id'] = OB.OBID
                        log.info('Submitting execution history to KPFCC API')
                        log.debug(f"  {history['id']}")
                        result = addObservingBlockHistory(history)
                        log.debug(f"KPFCC API Response: {result}")
                    if scriptstop:
                        raise ScriptStopTriggered("SCRIPTSTOP triggered")
                except ScriptStopTriggered as scriptstop:
                    log.error('Script Stop Triggered')
                    break
                except Exception as e:
                    log.error('Exception encountered during ExecuteSci')
                    log.error(e)
                    break
            # -------------------------------------------------------------
            # Cleanup After Science
            # -------------------------------------------------------------
            log.info(f'Cleaning up after Observations')
            CleanupAfterScience.execute(args, OB=OB)

        clear_script_keywords()

    @classmethod
    def post_condition(cls, args, OB=None):
        pass

    @classmethod
    def add_cmdline_args(cls, parser):
        parser.add_argument('--leave_lamps_on', dest="leave_lamps_on",
            default=False, action="store_true",
            help='Leave the calibration lamps on after cleanup phase?')
        parser.add_argument('--waitforscript', dest="waitforscript",
            default=False, action="store_true",
            help='Wait for running script to end before starting?')
        parser.add_argument('--scheduled', dest="scheduled",
            default=False, action="store_true",
            help='Script is scheduled and should obey ALLOWSCHEDULEDCALS keyword')
        return super().add_cmdline_args(parser)
