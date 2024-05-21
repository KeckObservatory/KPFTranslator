import os
import time
from pathlib import Path
import datetime
import traceback

import ktl

from kpf.KPFTranslatorFunction import KPFTranslatorFunction
from kpf import (log, KPFException, FailedPreCondition, FailedPostCondition,
                 FailedToReachDestination, check_input)
from kpf.scripts import (set_script_keywords, clear_script_keywords,
                         add_script_log, check_script_running)
from kpf.scripts import (register_script, obey_scriptrun, check_scriptstop,
                         add_script_log)
from kpf.scripts.ExecuteCal import ExecuteCal
from kpf.scripts.CleanupAfterCalibrations import CleanupAfterCalibrations
from kpf.socal.WaitForSoCalOnTarget import WaitForSoCalOnTarget


class RunSoCalObservingLoop(KPFTranslatorFunction):
    '''

    ARGS:
    =====
    
    '''
    @classmethod
    def pre_condition(cls, args, logger, cfg):
        pass

    @classmethod
    @add_script_log(Path(__file__).name.replace(".py", ""))
    def perform(cls, args, logger, cfg):
        AUTONOMOUS = ktl.cache('kpfsocal', 'AUTONOMOUS')
        AUTONOMOUS.monitor()
        SCRIPTNAME = ktl.cache('kpfconfig', 'SCRIPTNAME')
        SCRIPTNAME.monitor()
        SCRIPTPID = ktl.cache('kpfconfig', 'SCRIPTPID')
        SCRIPTPID.monitor()

        # Start Loop
        max_wait_per_iteration = 60
        start_time = args.get('StartTimeHST', 9)
        end_time = args.get('EndTimeHST', 12)
        now = datetime.datetime.now()
        now_decimal = (now.hour + now.minute/60 + now.second/3600)

        if now_decimal < start_time:
            log.info('Waiting for SoCal window start time')
            time.sleep((start_time-now_decimal)*3600)
        elif now_decimal > end_time:
            log.info("End time for today's SoCal window has passed")
            return
        elif AUTONOMOUS.ascii == 'Manual':
            log.warning('SoCal is in Manual mode. Exiting.')
            return

        if SCRIPTPID.binary >= 0:
            waittime = (end_time-now_decimal)*3600 - 600
            log.warning(f'Script is currently running: {SCRIPTNAME.ascii} {SCRIPTPID.binary}')
            log.info(f'Waiting for kpfconfig.SCRIPTPID to be clear')
            SCRIPTPID.waitFor("==-1", timeout=waittime)

        log.info('Starting SoCal observation loop')
        check_script_running()
        set_script_keywords(Path(__file__).name, os.getpid())
        check_scriptstop()

        if now_decimal > start_time and now_decimal < end_time:
            on_target = WaitForSoCalOnTarget.execute({'timeout': max_wait_per_iteration})
            log.debug(f'SoCal on target: {on_target}')
            if on_target == True:
                # Observe the Sun
                observation = {'Template_Name': 'kpf_lamp',
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
                               'CalND1': args.get('SoCalND1', 'OD 0.1'),
                               'CalND2': args.get('SoCalND2', 'OD 0.1'),
                               'ExpTime': args.get('SoCalExpTime', 12),
                               'nExp': 5,
                               'SSS_Science': True,
                               'SSS_Sky': True,
                               'TakeSimulCal': True,
                               'nointensemon': True,
                               }
            else:
                # Take etalon calibrations
                observation = {'Template_Name': 'kpf_lamp',
                               'Template_Version': '1.0',
                               'TriggerCaHK': True,
                               'TimedShutter_CaHK': True,
                               'TriggerGreen': True,
                               'TriggerRed': True,
                               'TriggerExpMeter': False,
                               'RunAgitator': True,
                               'CalSource': 'EtalonFiber',
                               'Object': 'autocal-etalon-all',
                               'CalND1': args.get('EtalonND1', 'OD 0.1'),
                               'CalND2': args.get('EtalonND2', 'OD 0.1'),
                               'ExpTime': args.get('EtalonExpTime', 60),
                               'nExp': 3,
                               'SSS_Science': True,
                               'SSS_Sky': True,
                               'TakeSimulCal': True,
                               'nointensemon': True,
                               }
 
            try:
                check_scriptstop()
                ExecuteCal.execute(observation)
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
        # SoCal Parameters
        parser.add_argument('--SoCalExpTime', dest="SoCalExpTime",
                            type=float, default=12,
                            help='Exposure time for SoCal exposures.')
        parser.add_argument('--SoCalND1', dest="SoCalND1",
                            type=str, default='OD 0.1',
                            choices=["OD 0.1", "OD 1.0", "OD 1.3", "OD 2.0",
                                     "OD 3.0", "OD 4.0"],
                            help='ND1 Filter to use for SoCal.')
        parser.add_argument('--SoCalND2', dest="SoCalND2",
                            type=str, default='OD 0.1',
                            choices=["OD 0.1", "OD 0.3", "OD 0.5", "OD 0.8",
                                     "OD 1.0", "OD 4.0"],
                            help='ND2 Filter to use for SoCal.')
        # Etalon Parameters
        parser.add_argument('--EtalonExpTime', dest="EtalonExpTime",
                            type=float, default=60,
                            help='Exposure time for Etalon exposures.')
        parser.add_argument('--EtalonND1', dest="EtalonND1",
                            type=str, default='OD 0.1',
                            choices=["OD 0.1", "OD 1.0", "OD 1.3", "OD 2.0",
                                     "OD 3.0", "OD 4.0"],
                            help='ND1 Filter to use for Etalon.')
        parser.add_argument('--EtalonND2', dest="EtalonND2",
                            type=str, default='OD 0.1',
                            choices=["OD 0.1", "OD 0.3", "OD 0.5", "OD 0.8",
                                     "OD 1.0", "OD 4.0"],
                            help='ND2 Filter to use for Etalon.')
        return super().add_cmdline_args(parser, cfg)
