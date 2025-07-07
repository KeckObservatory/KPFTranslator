import os
import time
from pathlib import Path
import datetime
import traceback
import yaml

import ktl

from kpf import log, cfg
from kpf.exceptions import *
from kpf.KPFTranslatorFunction import KPFFunction, KPFScript
from kpf.scripts import (set_script_keywords, clear_script_keywords,
                         add_script_log, check_script_running)
from kpf.scripts import (register_script, obey_scriptrun, check_scriptstop,
                         add_script_log)
from kpf.ObservingBlocks.ObservingBlock import ObservingBlock
from kpf.fiu.ConfigureFIU import ConfigureFIU
from kpf.scripts.ExecuteCal import ExecuteCal
from kpf.scripts.CleanupAfterCalibrations import CleanupAfterCalibrations
from kpf.scripts.EstimateOBDuration import EstimateOBDuration
from kpf.socal.ParkSoCal import ParkSoCal
from kpf.socal.SoCalStartAutonomous import SoCalStartAutonomous
from kpf.socal.WaitForSoCalOnTarget import WaitForSoCalOnTarget


class RunSoCalObservingLoop(KPFScript):
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

    ## Arguments
    * __StartTimeHST__ - `float` The time (in decimal hours HST) to begin observing.
    * __EndTimeHST__ - `float` The time (in decimal hours HST) to end observing.
    * __park__ - `bool` If True, the script will park SoCal when complete.
    * __scheduled__ - `bool` If True, the script will not run if the keyword
                `kpfconfig.ALLOWSCHEDULEDCALS` is "No".
    '''
    @classmethod
    def pre_condition(cls, args, OB=None):
        SoCalOBfile = Path(cfg.get('SoCal', 'SoCalOB', fallback='/tmp/SoCalOB.yaml'))
        if SoCalOBfile.exists() == False:
            raise PreConfitionFailed(f'SoCal OB File does not exist: {SoCalOBfile}')

    @classmethod
    @add_script_log(Path(__file__).name.replace(".py", ""))
    def perform(cls, args, OB=None):
        # Check the ALLOWSCHEDULEDCALS value
        if args.get('scheduled', True) is True:
            ALLOWSCHEDULED = ktl.cache('kpfconfig', 'ALLOWSCHEDULEDCALS')
            if ALLOWSCHEDULED.read() == 'No':
                log.warning(f'Not running {cls.__name__} because ALLOWSCHEDULEDCALS is No')
                return

        # Start SoCal in autonomous mode
        SoCalStartAutonomous.execute({})

        # If requested wait for an existing script to complete
        if args.get('waitforscript', False) is True:
            newscript = f'{Path(__file__).name.replace(".py", "")}(PID {os.getpid()})'
            wait_for_script(newscript=newscript)
        check_script_running()
        set_script_keywords(Path(__file__).name, os.getpid())

        log.info('-------------------------')
        log.info(f"Running {cls.__name__}")
        log.info('-------------------------')
        SoCalOBfile = Path(cfg.get('SoCal', 'SoCalOB', fallback='/tmp/SoCalOB.yaml'))
        log.info(f"Loading SoCal OB from {SoCalOBfile}")
        SoCal_OB = ObservingBlock(SoCalOBfile)

        # Estimate time to Run SoCal OB
        SoCal_duration = EstimateOBDuration.execute({}, OB=SoCal_OB)

        # Estimate time to run Etalon OB
        SLEWCALFILE = ktl.cache('kpfconfig', 'SLEWCALFILE')
        slewcal_OBfile = Path(SLEWCALFILE.read())
        log.debug(f"Reading: {slewcal_OBfile}")
        with open(slewcal_OBfile, 'r') as file:
            slewcal_OBdict = yaml.safe_load(file)
            SlewCal_OB = ObservingBlock(slewcal_OBdict)
        Etalon_duration = EstimateOBDuration.execute({}, OB=SlewCal_OB)
        log.debug(f"Estimated Etalon observation time = {Etalon_duration}")


        # Start Loop
        start_time = args.get('StartTimeHST', 9)
        # End time subtracts off max duration of observation and 3 minutes of buffer
        end_time = args.get('EndTimeHST', 12) - max([SoCal_duration, Etalon_duration])/3600 - 0.05
        now = datetime.datetime.now()
        now_decimal = (now.hour + now.minute/60 + now.second/3600)
        if now_decimal < start_time:
            wait = (start_time-now_decimal)*3600
            log.info(f'Waiting {wait:.0f}s for SoCal window start time')
            time.sleep(wait)
        elif now_decimal > end_time:
            log.info("End time for today's SoCal window has passed")
            return

        ConfigureFIU.execute({'mode': 'Calibration'})
        log.info(f'Starting SoCal observation loop')
        log.info(f'Start time: {start_time:.2f} HST')
        log.info(f'End Time: {end_time:.2f} HST')

        check_scriptstop()

        nSoCalObs = 0
        nEtalonObs = 0

        now = datetime.datetime.now()
        now_decimal = (now.hour + now.minute/60 + now.second/3600)
        while now_decimal >= start_time and now_decimal < end_time:
            log.debug('Checking if SoCal is on the Sun')
            on_target = WaitForSoCalOnTarget.execute({'timeout': 30})
            OB = {True: SoCal_OB, False: SlewCal_OB}[on_target]
            log.info(f'SoCal on target: {on_target}')
            try:
                check_scriptstop()
                for i,calibration in enumerate(OB.Calibrations):
                    ExecuteCal.execute(calibration.to_dict())
                if on_target == True:
                    nSoCalObs += 1
                else:
                    nEtalonObs += 1
            except ScriptStopTriggered as e:
                raise e
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

            check_scriptstop()

            # Update loop inputs
            now = datetime.datetime.now()
            now_decimal = (now.hour + now.minute/60 + now.second/3600)

        log.info('SoCal observation loop completed')
        log.info(f'Executed {nSoCalObs} SoCal sequences')
        log.info(f'Executed {nEtalonObs} Etalon sequences')

        # Cleanup
        try:
            CleanupAfterCalibrations.execute({}, OB=SlewCal_OB)
        except Exception as e:
            log.error("CleanupAfterCalibrations failed:")
            log.error(e)
            traceback_text = traceback.format_exc()
            log.error(traceback_text)
            clear_script_keywords()
            # Email error to kpf_info
            try:
                msg = [f'{type(e)}',
                       f'{traceback_text}',
                       '',
                       f'{OB}']
                SendEmail.execute({'Subject': 'CleanupAfterCalibrations Failed',
                                   'Message': '\n'.join(msg)})
            except Exception as email_err:
                log.error(f'Sending email failed')
                log.error(email_err)

        # Park SoCal?
        if args.get('park', False) == True:
            ParkSoCal.execute({})

    @classmethod
    def post_condition(cls, args, OB=None):
        pass

    @classmethod
    def add_cmdline_args(cls, parser):
        parser.add_argument('StartTimeHST', type=float,
            help='Start of daily observing window in decimal hours HST.')
        parser.add_argument('EndTimeHST', type=float,
            help='End of daily observing window in decimal hours HST.')
        parser.add_argument("--park", dest="park",
            default=False, action="store_true",
            help="Close and park SoCal when done?")
        parser.add_argument('--waitforscript', dest="waitforscript",
            default=False, action="store_true",
            help='Wait for running script to end before starting?')
        parser.add_argument("--notscheduled", dest="scheduled",
            default=True, action="store_false",
            help="Do not respect the kpfconfig.ALLOWSCHEDULEDCALS flag.")
        return super().add_cmdline_args(parser)
