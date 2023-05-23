from time import sleep
from pathlib import Path
import os
import traceback

import ktl

from kpf.KPFTranslatorFunction import KPFTranslatorFunction
from kpf import (log, KPFException, FailedPreCondition, FailedPostCondition,
                 FailedToReachDestination, check_input)
from kpf.scripts import (set_script_keywords, clear_script_keywords,
                         add_script_log, check_script_running)
from kpf.scripts.ConfigureForCalibrations import ConfigureForCalibrations
from kpf.scripts.ExecuteDark import ExecuteDark
from kpf.scripts.ExecuteCal import ExecuteCal
from kpf.scripts.CleanupAfterCalibrations import CleanupAfterCalibrations
from kpf.spectrograph.SetSourceSelectShutters import SetSourceSelectShutters
from kpf.spectrograph.SetTimedShutters import SetTimedShutters
from kpf.calbench.SetCalSource import SetCalSource
from kpf.calbench.SetFlatFieldFiberPos import SetFlatFieldFiberPos
from kpf.utils.SendEmail import SendEmail


class RunCalOB(KPFTranslatorFunction):
    '''Script to run a full Calibration OB from the command line.

    This must have arguments as input, typically from a file using the `-f`
    command line tool.

    Not intended to be called by DDOI's execution engine. This script replaces
    the DDOI Script.

    This script is abortable.  When `.abort_execution()` is invoked, the
    `kpconfig.SCRIPTSTOP` is set to Yes.  This script checked for this value at
    various locations in the script.  As a result, the script will not stop
    immediately, but will stop when it reaches a breakpoint.

    ARGS:
    =====
    None
    '''
    abortable = True

    @classmethod
    def pre_condition(cls, OB, logger, cfg):
        check_input(OB, 'Template_Name', allowed_values=['kpf_cal'])
        check_input(OB, 'Template_Version', version_check=True, value_min='0.5')

    @classmethod
    @add_script_log(Path(__file__).name.replace(".py", ""))
    def perform(cls, OB, logger, cfg):
        log.info('-------------------------')
        log.info(f"Running {cls.__name__}")
        for key in OB:
            if key not in ['SEQ_Darks', 'SEQ_Calibrations']:
                log.debug(f"  {key}: {OB[key]}")
            else:
                log.debug(f"  {key}:")
                for entry in OB[key]:
                    log.debug(f"    {entry}")
        log.info('-------------------------')

        # Configure: Turn on Lamps
        try:
            ConfigureForCalibrations.execute(OB)
        except Exception as e:
            log.error('ConfigureForCalibrations Failed')
            log.error(e)
            log.error('Running CleanupAfterCalibrations and exiting')
            CleanupAfterCalibrations.execute(OB)
            # Email error to kpf_info
            try:
                msg = [f'{type(e)}',
                       f'{traceback.format_exc()}',
                       '',
                       f'{OB}']
                SendEmail.execute({'Subject': 'ConfigureForCalibrations Failed',
                                   'Message': '\n'.join(msg)})
            except Exception as email_err:
                log.error(f'Sending email failed')
                log.error(email_err)
            raise e

        check_script_running()
        set_script_keywords(Path(__file__).name, os.getpid())

        # Execute the Dark Sequence
        try:
            darks = OB.get('SEQ_Darks', [])
            if len(darks) > 0:
                log.info(f"Setting source select shutters")
                SetSourceSelectShutters.execute({}) # No args defaults all to false
                log.info(f"Setting timed shutters")
                SetTimedShutters.execute({}) # No args defaults all to false
                log.info(f"Setting OCTAGON to Home position")
                SetCalSource.execute({'CalSource': 'Home'})
                log.info(f"Setting FlatField Fiber position to 'Blank'")
                SetFlatFieldFiberPos.execute({'FF_FiberPos': 'Blank'})
            for dark in darks:
                # Wrap in try/except so that cleanup happens
                dark['Template_Name'] = 'kpf_dark'
                dark['Template_Version'] = OB['Template_Version']
                ExecuteDark.execute(dark)
        except Exception as e:
            log.error("ExecuteDarks failed:")
            log.error(e)
            clear_script_keywords()
            # Email error to kpf_info
            try:
                msg = [f'{type(e)}',
                       f'{traceback.format_exc()}',
                       '',
                       f'{OB}']
                SendEmail.execute({'Subject': 'ExecuteDarks Failed',
                                   'Message': '\n'.join(msg)})
            except Exception as email_err:
                log.error(f'Sending email failed')
                log.error(email_err)
            # Cleanup
            CleanupAfterCalibrations.execute(OB)
            raise e

        # Execute the Cal Sequence
        try:
            cals = OB.get('SEQ_Calibrations', [])
            for cal in cals:
                # No need to specify TimedShutter_CaHK in OB/calibration
                cal['TimedShutter_CaHK'] = OB['TriggerCaHK']
                log.debug(f"Automatically setting TimedShutter_CaHK: {cal['TimedShutter_CaHK']}")
                cal['Template_Name'] = 'kpf_lamp'
                cal['Template_Version'] = OB['Template_Version']
                ExecuteCal.execute(cal)
        except Exception as e:
            log.error("ExecuteCal failed:")
            log.error(e)
            clear_script_keywords()
            # Email error to kpf_info
            traceback_text = traceback.format_exc()
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
            CleanupAfterCalibrations.execute(OB)
            raise e

        clear_script_keywords()

        # Cleanup: Turn off lamps
        try:
            CleanupAfterCalibrations.execute(OB)
        except Exception as e:
            log.error("CleanupAfterCalibrations failed:")
            log.error(e)
            # Email error to kpf_info
            traceback_text = traceback.format_exc()
            try:
                msg = [f'{type(e)}',
                       f'{traceback.format_exc()}',
                       '',
                       f'{OB}']
                SendEmail.execute({'Subject': 'CleanupAfterCalibrations Failed',
                                   'Message': '\n'.join(msg)})
            except Exception as email_err:
                log.error(f'Sending email failed')
                log.error(email_err)
            raise e

    @classmethod
    def post_condition(cls, OB, logger, cfg):
        pass

    @classmethod
    def add_cmdline_args(cls, parser, cfg=None):
        parser.add_argument('--leave_lamps_on', dest="leave_lamps_on",
                            default=False, action="store_true",
                            help='Leave the lamps on after cleanup phase?')
        parser.add_argument('--nointensemon', dest="nointensemon",
                            default=False, action="store_true",
                            help='Skip the intensity monitor measurement?')
        return super().add_cmdline_args(parser, cfg)
