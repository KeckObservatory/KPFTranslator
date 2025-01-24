import sys
import time
import os
import traceback
from pathlib import Path

from kpf.KPFTranslatorFunction import KPFScript 
from kpf import (log, KPFException, FailedPreCondition, FailedPostCondition,
                 FailedToReachDestination, ScriptStopTriggered)
from kpf.scripts import obey_scriptrun, register_script, add_script_log
from kpf.ObservingBlocks.ObservingBlock import ObservingBlock
from kpf.utils.SendTargetToMagiq import SendTargetToMagiq
from kpf.scripts.ConfigureForCalibrations import ConfigureForCalibrations
from kpf.scripts.ExecuteCal import ExecuteCal
from kpf.scripts.CleanupAfterCalibrations import CleanupAfterCalibrations
from kpf.scripts.ConfigureForAcquisition import ConfigureForAcquisition
from kpf.scripts.WaitForConfigureAcquisition import WaitForConfigureAcquisition
from kpf.scripts.ConfigureForScience import ConfigureForScience
from kpf.scripts.WaitForConfigureScience import WaitForConfigureScience
from kpf.scripts.ExecuteSci import ExecuteSci
from kpf.scripts.CleanupAfterScience import CleanupAfterScience


class RunOB(KPFScript):
    '''Script to run an OB.

    ARGS:
    =====
    * __leave_lamps_on__ - `bool` Leave calibration lamps on when done?
    * __OB__ - `ObservingBlock` or `dict` A valid observing block (OB).
    '''
    @classmethod
    @obey_scriptrun
    def pre_condition(cls, args, OB=None):
        # Read the OB
        if isinstance(OB, dict):
            OB = ObservingBlock(OB)
        elif isinstance(OB, ObservingBlock):
            pass
        else:
            raise FailedPreCondition('Input must be dict or ObservingBlock')
        # Validate the OB
        OB.validate()

    @classmethod
    @register_script(Path(__file__).name, os.getpid())
    @add_script_log(Path(__file__).name.replace(".py", ""))
    def perform(cls, args, OB=None):
        log.info('-------------------------')
        log.info(f"Running {cls.__name__}")
        log.info('-------------------------')
        if isinstance(OB, dict):
            OB = ObservingBlock(OB)

        if OB.Target is not None:
            log.info(f'Sending target info to Magiq')
            SendTargetToMagiq.execute(OB)
        if len(OB.Calibrations) > 0:
            log.info(f'Executing Calibrations')
            ConfigureForCalibrations.execute(OB)
            for i,calibration in enumerate(OB.Calibrations):
                log.info(f'Executing Calibration {i+1}/{len(OB.Calibrations)}')
                ExecuteCal.execute(calibration.to_dict())
            log.info(f'Cleaning up after Calibrations')
            CleanupAfterCalibrations.execute(OB)
        if OB.Target is not None:
            log.info(f'Configuring for Acquisition')
            ConfigureForAcquisition.execute(OB)
            WaitForConfigureAcquisition.execute(OB)
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
    def post_condition(cls, args, OB=None):
        pass

    @classmethod
    def add_cmdline_args(cls, parser):
        parser.add_argument('--leave_lamps_on', dest="leave_lamps_on",
                            default=False, action="store_true",
                            help='Leave the calibration lamps on after cleanup phase?')
        return super().add_cmdline_args(parser)
