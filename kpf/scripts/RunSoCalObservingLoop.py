import os
import time
from pathlib import Path
import datetime
import traceback

import ktl

from kpf.KPFTranslatorFunction import KPFTranslatorFunction
from kpf import (log, KPFException, FailedPreCondition, FailedPostCondition,
                 FailedToReachDestination, check_input, ScriptStopTriggered)
from kpf.scripts import (set_script_keywords, clear_script_keywords,
                         add_script_log, check_script_running)
from kpf.scripts import (register_script, obey_scriptrun, check_scriptstop,
                         add_script_log)
from kpf.scripts.ExecuteCal import ExecuteCal
from kpf.scripts.CleanupAfterCalibrations import CleanupAfterCalibrations
from kpf.socal.ParkSoCal import ParkSoCal
from kpf.socal.SoCalStartAutonomous import SoCalStartAutonomous
from kpf.socal.WaitForSoCalOnTarget import WaitForSoCalOnTarget


class RunSoCalObservingLoop(KPFTranslatorFunction):
    '''This script runs a control loop to execute SoCal observations.

    When the script is invoked, it puts SoCal in AUTONOMOUS mode. This means
    that the SoCal dispatcher number 4 will handle opening the enclosure,
    acquiring and tracking the Sun, and will perform a weather safety shutdown
    if needed.  The AUTONOMOUS mode will respect the CAN_OPEN keyword as well,
    so that keyword will lock out SoCal motions if that is desired.

    The script takes two required inputs: a start and end time in decimal hours
    (in HST).  The start time can be after the invocation of this script.  This
    is in fact the recommended operational strategy as the SoCal AUTONOMOUS
    mode will then have time to open and acquire the Sun before observations
    start.

    If needed, the script will wait until the start time before taking further
    actions (beyond setting AUTONOMOUS). Once the start time has passed, the
    script will check the `kpfconfig.SCRIPT%` keywords to see if something is
    currently running.  If so, it will wait for the script keywords to clear
    before starting operations.

    Next the script will try to determine if SoCal is successfully observing
    the Sun by invoking the `WaitForSoCalOnTarget` script.

    If SoCal is on target, then a short observation of the Sun is performed.
    Some of the parameters can be modified in the `KPFTranslator` configuration
    file (`kpf_inst_config.ini`). This observation, as currently configured,
    takes about 15 minutes to complete.

    If SoCal is not on target (according to the `WaitForSoCalOnTarget` script),
    then an Etalon calibration set is taken.  This is a way to make use of time
    that would otherwise be unproductive. This etalon script also takes around
    15 minutes or a bit less to complete.

    Once either of the two observations above has completed, the script repeats
    the loop as long as there is enough time before the end time to complete a
    SoCal observation.

    Once the end time has passed, the system will perform basic cleanup of KPF,
    then it will park SoCal using `ParkSoCal` if the park flag is set.

    ARGS:
    =====
    :StartTimeHST: `float` The time (in decimal hours HST) to begin observing.
    :EndTimeHST: `float` The time (in decimal hours HST) to end observing.
    :park: `bool` If True, the script will park SoCal when complete.
    :scheduled: `bool` If True, the script will not run if the keyword
                `kpfconfig.ALLOWSCHEDULEDCALS` is "No".
    '''
    @classmethod
    def pre_condition(cls, args, logger, cfg):
        pass

    @classmethod
    @add_script_log(Path(__file__).name.replace(".py", ""))
    def perform(cls, args, logger, cfg):
        # Check the ALLOWSCHEDULEDCALS value
        if args.get('scheduled', True) is True:
            ALLOWSCHEDULED = ktl.cache('kpfconfig', 'ALLOWSCHEDULEDCALS').read()
            if ALLOWSCHEDULED == 'No':
                return

        log.info('-------------------------')
        log.info(f"Running {cls.__name__}")
        log.info('-------------------------')

        # Prepare SoCal parameters to pass to ExecuteCal
        socal_ND1 = cfg.get('SoCal', 'ND1', fallback='OD 0.1')
        socal_ND2 = cfg.get('SoCal', 'ND2', fallback='OD 0.1')
        socal_ExpTime = cfg.getfloat('SoCal', 'ExpTime', fallback=12)
        SoCal_observation = {'Template_Name': 'kpf_lamp',
                             'Template_Version': '1.0',
                             'TargetName': 'Sun',
                             'TriggerCaHK': False,
                             'TimedShutter_CaHK': False,
                             'TriggerGreen': True,
                             'TriggerRed': True,
                             'TriggerExpMeter': False,
                             'RunAgitator': True,
                             'CalSource': 'SoCal-SciSky',
                             'Object': 'SoCal',
                             'CalND1': socal_ND1,
                             'CalND2': socal_ND2,
                             'ExpTime': socal_ExpTime,
                             'nExp': 15,
                             'SSS_Science': True,
                             'SSS_Sky': True,
                             'TakeSimulCal': True,
                             'nointensemon': True,
                             }
        readout_red = cfg.getfloat('time_estimates', f'readout_red', fallback=60)
        readout_green = cfg.getfloat('time_estimates', f'readout_green', fallback=60)
        readout_cahk = cfg.getfloat('time_estimates', 'readout_cahk', fallback=1)
        archon_time_shim = cfg.getfloat('times', 'archon_temperature_time_shim',
                             fallback=2)
        readout = max([readout_red, readout_green, readout_cahk])
        SoCal_duration = int(SoCal_observation['nExp'])*max([float(SoCal_observation['ExpTime']), archon_time_shim])
        SoCal_duration += int(SoCal_observation['nExp'])*readout
        log.debug(f"Estimated SoCal observation time = {SoCal_duration}")

        # Prepare Etalon parameters to pass to ExecuteCal
        Etalon_ND1 = cfg.get('SoCal', 'EtalonND1', fallback='OD 0.1')
        Etalon_ND2 = cfg.get('SoCal', 'EtalonND2', fallback='OD 0.1')
        Etalon_ExpTime = cfg.getfloat('SoCal', 'EtalonExpTime', fallback=60)
        Etalon_observation = {'Template_Name': 'kpf_lamp',
                              'Template_Version': '1.0',
                              'TriggerCaHK': True,
                              'TimedShutter_CaHK': True,
                              'TriggerGreen': True,
                              'TriggerRed': True,
                              'TriggerExpMeter': False,
                              'RunAgitator': True,
                              'CalSource': 'EtalonFiber',
                              'Object': 'autocal-etalon-all',
                              'CalND1': Etalon_ND1,
                              'CalND2': Etalon_ND2,
                              'ExpTime': Etalon_ExpTime,
                              'nExp': 8,
                              'SSS_Science': True,
                              'SSS_Sky': True,
                              'TakeSimulCal': True,
                              'nointensemon': True,
                              }
        Etalon_duration = int(Etalon_observation['nExp'])*max([float(Etalon_observation['ExpTime']), archon_time_shim])
        Etalon_duration += int(Etalon_observation['nExp'])*readout
        log.debug(f"Estimated Etalon observation time = {Etalon_duration}")

        # Start SoCal in autonomous mode
        SoCalStartAutonomous.execute({})

        # Start Loop
        max_wait_per_iteration = 60
        start_time = args.get('StartTimeHST', 9)
        end_time = args.get('EndTimeHST', 12) - SoCal_duration/3600 - 0.05
        now = datetime.datetime.now()
        now_decimal = (now.hour + now.minute/60 + now.second/3600)
        if now_decimal < start_time:
            wait = (start_time-now_decimal)*3600
            log.info(f'Waiting {wait:.0f}s for SoCal window start time')
            time.sleep(wait)
        elif now_decimal > end_time:
            log.info("End time for today's SoCal window has passed")
            return

        SCRIPTPID = ktl.cache('kpfconfig', 'SCRIPTPID')
        if SCRIPTPID.read(binary=True) >= 0:
            SCRIPTNAME = ktl.cache('kpfconfig', 'SCRIPTNAME').read()
            waittime = (end_time-now_decimal)*3600 - SoCal_duration - 180
            log.warning(f'Script is currently running: {SCRIPTNAME}')
            if waittime > 0:
                log.info(f'Waiting up to {waittime:.0f}s for running script to end')
                SCRIPTPID.waitFor("==-1", timeout=waittime)
                time.sleep(10) # time shim

        check_script_running()
        set_script_keywords(Path(__file__).name, os.getpid())
        log.info(f'Starting SoCal observation loop')
        log.info(f'Start time: {start_time:.2f} HST')
        log.info(f'End Time: {end_time:.2f} HST')

        check_scriptstop()

        nSoCalObs = 0
        nEtalonObs = 0

        now = datetime.datetime.now()
        now_decimal = (now.hour + now.minute/60 + now.second/3600)
        while now_decimal > start_time and now_decimal < end_time:
            log.debug('Checking if SoCal is on the Sun')
            on_target = WaitForSoCalOnTarget.execute({'timeout': max_wait_per_iteration})
            observation = {True: SoCal_observation, False: Etalon_observation}[on_target]
            log.info(f'SoCal on target: {on_target}')
            log.info(f"Executing {observation['Object']}")
            try:
                check_scriptstop()
                ExecuteCal.execute(observation)
                if on_target == True:
                    nSoCalObs += 1
                else:
                    nEtalonObs += 1
            except Exception as e:
                log.error("ExecuteCal failed:")
                log.error(e)
                traceback_text = traceback.format_exc()
                log.error(traceback_text)
                # Email error to kpf_info
                if not isinstance(e, ScriptStopTriggered):
                    try:
                        msg = [f'{type(e)}',
                               f'{traceback.format_exc()}',
                               '',
                               f'{OB}']
                        SendEmail.execute({'Subject': 'ExecuteCals Failed',
                                           'Message': '\n'.join(msg)})
                    except Exception as email_err:
                        log.error(f'Sending email failed')
                        log.error(email_err)
                # Cleanup
                clear_script_keywords()
                log.error('Running CleanupAfterCalibrations and exiting')
                CleanupAfterCalibrations.execute({})
                sys.exit(1)

            check_scriptstop()

            # Update loop inputs
            now = datetime.datetime.now()
            now_decimal = (now.hour + now.minute/60 + now.second/3600)

        log.info('SoCal observation loop completed')
        log.info(f'Executed {nSoCalObs} SoCal sequences')
        log.info(f'Executed {nEtalonObs} Etalon sequences')
        # Clear script keywords so that cleanup can start successfully
        clear_script_keywords()

        # Cleanup
        CleanupAfterCalibrations.execute(Etalon_observation)
        # Park SoCal?
        if args.get('park', False) == True:
            ParkSoCal.execute({})

    @classmethod
    def post_condition(cls, args, logger, cfg):
        pass

    @classmethod
    def add_cmdline_args(cls, parser, cfg=None):
        '''The arguments to add to the command line interface.
        '''
        parser.add_argument('StartTimeHST', type=float,
            help='Start of daily observing window in decimal hours HST.')
        parser.add_argument('EndTimeHST', type=float,
            help='End of daily observing window in decimal hours HST.')
        parser.add_argument("--park", dest="park",
            default=False, action="store_true",
            help="Close and park SoCal when done?")
        parser.add_argument("--notscheduled", dest="scheduled",
            default=True, action="store_false",
            help="Do not respect the kpfconfig.ALLOWSCHEDULEDCALS flag.")
        return super().add_cmdline_args(parser, cfg)
