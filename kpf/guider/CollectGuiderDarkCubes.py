import os
import time
from pathlib import Path
import datetime

import ktl

from kpf import log, cfg, check_input
from kpf.exceptions import *
from kpf.KPFTranslatorFunction import KPFFunction, KPFScript
from kpf.scripts import (register_script, obey_scriptrun, check_scriptstop,
                         add_script_log, clear_script_keywords)
from kpf.fiu.ConfigureFIU import ConfigureFIU
from kpf.guider.SetGuiderFPS import SetGuiderFPS
from kpf.guider.SetGuiderGain import SetGuiderGain
from kpf.guider.TakeGuiderCube import TakeGuiderCube
from kpf.spectrograph.SetSourceSelectShutters import SetSourceSelectShutters

class CollectGuiderDarkCubes(KPFFunction):
    '''Obtains CRED2 "trigger file" data cubes under dark conditions at each of
    the three gain settings for the detector.

    Sequence:
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
    @obey_scriptrun
    def pre_condition(cls, args):
        pass

    @classmethod
    @register_script(Path(__file__).name, os.getpid())
    @add_script_log(Path(__file__).name.replace(".py", ""))
    def perform(cls, args):
        output_file = Path('/s/sdata1701/CRED2DarkCubes/CRED2_dark_cubes.txt')
        OUTDIR = ktl.cache('kpfguide', 'OUTDIR')
        original_OUTDIR = OUTDIR.read()
        new_OUTDIR = str(output_file.parent)
        log.debug(f'Setting OUTDIR to {new_OUTDIR}')
        OUTDIR.write(new_OUTDIR)
        SENSORSETP = ktl.cache('kpfguide', 'SENSORSETP')
        SENSORTEMP = ktl.cache('kpfguide', 'SENSORTEMP')
        CONTINUOUS = ktl.cache('kpfguide', 'CONTINUOUS')
        kpfguide = ktl.cache('kpfguide')
        try:
            log.info('Taking CRED2 dark cubes')
            ConfigureFIU.execute({'mode': 'Stowed'})
            log.info('Cooling CRED2')
            SENSORSETP.write(-40)
            log.info('Waiting up to 10 minutes for detector to reach set point')
            reached_temp = SENSORTEMP.waitFor("<-39.9", timeout=600)
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

            CONTINUOUS.write('Active')
            SetGuiderFPS.execute({'GuideFPS': 100})

            for gain in ['high', 'medium', 'low']:
                log.info(f'Collecting {gain} gain cube')
                SetGuiderGain.execute({'GuideCamGain': gain})
                cube_file = TakeGuiderCube.execute({'duration': 10})
                with open(output_file, 'a') as f:
                    f.write(f"{gain:12s}, {cube_file}\n")
                check_scriptstop()
                time.sleep(30) # shim to give time to recover after writing cube
                check_scriptstop()

            for gain in ['high', 'medium', 'low']:
                sub_file = kpfguide[f'SUB_{gain.upper()}'].read()
                kpfguide[f'SUB_{gain.upper()}'].write('')
                log.info(f'Collecting {gain} gain cube without bias subtraction')
                SetGuiderGain.execute({'GuideCamGain': gain})
                cube_file = TakeGuiderCube.execute({'duration': 10})
                with open(output_file, 'a') as f:
                    gain_string = f'{gain}_nosub'
                    f.write(f"{gain_string:12s}, {cube_file}\n")
                kpfguide[f'SUB_{gain.upper()}'].write(sub_file)
                check_scriptstop()
                time.sleep(30) # shim to give time to recover after writing cube
                check_scriptstop()


        except Exception as e:
            log.error('Error running CollectGuiderDarkCubes')
            log.debug(e)

        log.info('Resetting CRED2 temperature set point to 0')
        SENSORSETP.write(0)
        log.debug(f'Setting OUTDIR to {original_OUTDIR}')
        OUTDIR.write(original_OUTDIR)
        clear_script_keywords()


    @classmethod
    def post_condition(cls, args):
        pass
