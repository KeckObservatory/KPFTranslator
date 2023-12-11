import time
from pathlib import Path

import ktl

from kpf.KPFTranslatorFunction import KPFTranslatorFunction
from kpf import (log, KPFException, FailedPreCondition, FailedPostCondition,
                 FailedToReachDestination, check_input)
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
        pass

    @classmethod
    def perform(cls, args, logger, cfg):
        SENSORSETP = ktl.cache('kpfguide', 'SENSORSETP')

        log.info('Taking CRED2 dark cubes')
        log.info('Cooling CRED2')
        SENSORSETP.write(-40)
        ConfigureFIU.execute({'mode': 'Stowed'})
        reached_temp = SENSORSETP.waitFor("<-39.9", timeout=600)
        if reached_temp == False:
            log.error('CRED2 failed to reach set point. Exiting.')
            SENSORSETP.write(0)
            return
        log.debug('Waiting additional time for temperature to stabilize')
        time.sleep(60) # shim to give time to stabilize

        log.debug('Closing source shutters')
        SetSourceSelectShutters.execute({})

        SetGuiderFPS.execute({'GuideFPS': 100})

        SetGuiderGain.execute({'GuideCamGain': 'high'})
        cube_file_high = TakeGuiderCube.execute({'duration': 10})
        time.sleep(30) # shim to give time for system to recover

        SetGuiderGain.execute({'GuideCamGain': 'medium'})
        cube_file_medium = TakeGuiderCube.execute({'duration': 10})
        time.sleep(30) # shim to give time for system to recover

        SetGuiderGain.execute({'GuideCamGain': 'low'})
        cube_file_low = TakeGuiderCube.execute({'duration': 10})
        time.sleep(30) # shim to give time for system to recover

        log.info('Resetting CRED2 temperature set point to 0')
        SENSORSETP.write(0)

        output_file = Path('/s/sdata1701/KPFTranslator_logs/CRED2_dark_cubes.txt')
        with open(output_file, 'a') as f:
            f.write(f"high, {cube_file_high}\n")
            f.write(f"medium, {cube_file_medium}\n")
            f.write(f"low, {cube_file_low}\n")


    @classmethod
    def post_condition(cls, args, logger, cfg):
        pass

    @classmethod
    def add_cmdline_args(cls, parser, cfg=None):
        '''The arguments to add to the command line interface.
        '''
        parser.add_argument('duration', type=float,
                            help='The duration in seconds')
        parser.add_argument("--noTRIGCUBE", dest="ImageCube",
                            default=True, action="store_false",
                            help="Collect the full image cube?")
        return super().add_cmdline_args(parser, cfg)
