import os
import time
from pathlib import Path
import datetime

import ktl

from kpf.KPFTranslatorFunction import KPFTranslatorFunction
from kpf import (log, KPFException, FailedPreCondition, FailedPostCondition,
                 FailedToReachDestination, check_input)
from kpf.scripts import (register_script, obey_scriptrun, check_scriptstop,
                         add_script_log, clear_script_keywords)
from kpf.fiu.ConfigureFIU import ConfigureFIU
from kpf.guider.SetGuiderFPS import SetGuiderFPS
from kpf.guider.SetGuiderGain import SetGuiderGain
from kpf.guider.TakeGuiderCube import TakeGuiderCube
from kpf.spectrograph.SetSourceSelectShutters import SetSourceSelectShutters

class CollectGuiderDarkCubes(KPFTranslatorFunction):
    '''

    - Set FIU to Stowed
    - Set kpfguide.SENSORSETP = -40
    - Wait for temperature to reach target
    - modify -s kpfexpose SRC_SHUTTERS=''
    - Set FPS = 100
    - Set GAIN = High
    - Take 10s trigger cube
    - Set GAIN = High
    - Take 10s trigger cube
    - Set GAIN = Low
    - Take 10s trigger cube
    - Set kpfguide.SENSORSETP = 0

    ARGS:
    =====
    None
    '''
    @classmethod
    def pre_condition(cls, args, logger, cfg):
        check_script_running()

    @classmethod
    @add_script_log(Path(__file__).name.replace(".py", ""))
    def perform(cls, args, logger, cfg):
        set_script_keywords(Path(__file__).name, os.getpid())

        output_file = Path('/s/sdata1701/KPFTranslator_logs/CRED2_dark_cubes.txt')
        SENSORSETP = ktl.cache('kpfguide', 'SENSORSETP')
        try:
            log.info('Taking CRED2 dark cubes')
            log.info('Cooling CRED2')
            SENSORSETP.write(-40)
            ConfigureFIU.execute({'mode': 'Stowed'})
            reached_temp = SENSORSETP.waitFor("<-39.9", timeout=600)
            if reached_temp == False:
                log.error('CRED2 failed to reach set point. Exiting.')
                SENSORSETP.write(0)
                return

            check_scriptstop()

            log.debug('Waiting additional time for temperature to stabilize')
            time.sleep(60) # shim to give time to stabilize

            check_scriptstop()

            log.debug('Closing source shutters')
            SetSourceSelectShutters.execute({})

            SetGuiderFPS.execute({'GuideFPS': 100})

            for gain in ['high', 'medium', 'low']:
                log.info(f'Collecting {gain} gain cube')
                SetGuiderGain.execute({'GuideCamGain': gain})
                cube_file = TakeGuiderCube.execute({'duration': 10})
                with open(output_file, 'a') as f:
                    f.write(f"{gain:6s}, {cube_file}\n")
                check_scriptstop()
                time.sleep(30) # shim to give time to recover after writing cube
                check_scriptstop()

        except Exception as e:
            log.error('Error running CollectGuiderDarkCubes')
            log.debug(e)

        log.info('Resetting CRED2 temperature set point to 0')
        SENSORSETP.write(0)
        clear_script_keywords()


    @classmethod
    def post_condition(cls, args, logger, cfg):
        pass
