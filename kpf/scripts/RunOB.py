import sys
import time
import os
import traceback
from pathlib import Path

import ktl

from kpf.KPFTranslatorFunction import KPFTranslatorFunction
from kpf import (log, KPFException, FailedPreCondition, FailedPostCondition,
                 FailedToReachDestination, ScriptStopTriggered)
from kpf.scripts import (set_script_keywords, clear_script_keywords,
                         add_script_log, check_script_running, check_scriptstop)
from kpf.ObservingBlocks.ObservingBlock import ObservingBlock

from kpf.utils.SendTargetToMagiq import SendTargetToMagiq

from kpf.scripts.ConfigureForCalibrations import ConfigureForCalibrations
from kpf.scripts.ExecuteCal import ExecuteCal
from kpf.scripts.CleanupAfterCalibrations import CleanupAfterCalibrations

from kpf.scripts.ConfigureForAcquisition import ConfigureForAcquisition
from kpf.scripts.WaitForConfigureAcquisition import WaitForConfigureAcquisition

from kpf.scripts.ConfigureForScience import ConfigureForScience
from kpf.scripts.WaitForConfigureScience import WaitForConfigureScience
from kpf.scripts.CleanupAfterScience import CleanupAfterScience
from kpf.scripts.ExecuteSci import ExecuteSci


class RunSciOB(KPFTranslatorFunction):
    '''Script to run an OB from the command line.

    ARGS:
    =====
    * __OB__ - `ObservingBlock` A fully specified observing block (OB).
    '''
    @classmethod
    def pre_condition(cls, OB):
        if not isinstance(OB, ObservingBlock):
            raise FailedPreCondition('Input is not an ObservingBlock')
        if not OB.validate():
            raise FailedPreCondition('Input ObservingBlock is invalid')

    @classmethod
    @add_script_log(Path(__file__).name.replace(".py", ""))
    def perform(cls, OB):
        log.info('-------------------------')
        log.info(f"Running {cls.__name__}")
        log.info('-------------------------')

        if OB.Target is not None:
            log.info(f'Sending target info to Magiq')
            SendTargetToMagiq.execute(OB.Target)
        if len(OB.Calibrations) > 0:
            log.info(f'Executing Calibrations')
            ConfigureForCalibrations.execute(OB.Calibrations)
            for i,calibration in enumerate(OB.Calibrations):
                log.info(f'Executing Calibration {i+1}/{len(OB.Calibrations)}')
                ExecuteCal.execute(calibration)
            log.info(f'Cleaning up after Calibrations')
            CleanupAfterCalibrations.execute(OB.Calibrations)
        if OB.Target is not None:
            log.info(f'Configuring for Acquisition')
            ConfigureForAcquisition.execute(OB.Target)
            WaitForConfigureAcquisition.execute(OB.Target)
        if len(OB.Observations) > 0:
            log.info(f'Configuring for Observations')
            ConfigureForScience.execute(OB.Observations)
            WaitForConfigureScience.execute(OB.Observations)
            for i,observation in enumerate(OB.Observations):
                log.info(f'Executing Observation {i+1}/{len(OB.Observations)}')
                ExecuteSci.execute(observation)
            log.info(f'Cleaning up after Observations')
            CleanupAfterScience.execute(OB.Observations)

    @classmethod
    def post_condition(cls, OB):
        pass

    @classmethod
    def add_cmdline_args(cls, parser, cfg=None):
        parser.add_argument('--leave_lamps_on', dest="leave_lamps_on",
                            default=False, action="store_true",
                            help='Leave the calibration lamps on after cleanup phase?')
        parser.add_argument('--nointensemon', dest="nointensemon",
                            default=False, action="store_true",
                            help='Skip the intensity monitor measurement on calibration frames?')
        return super().add_cmdline_args(parser, cfg)
