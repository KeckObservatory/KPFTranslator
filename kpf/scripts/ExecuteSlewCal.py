import os
from time import sleep
from packaging import version
from pathlib import Path

import ktl

from kpf import log, cfg, check_input
from kpf.exceptions import *
from kpf.KPFTranslatorFunction import KPFFunction, KPFScript
from kpf.scripts import (register_script, obey_scriptrun, check_scriptstop,
                         add_script_log)
from kpf.scripts import (set_script_keywords, clear_script_keywords,
                         check_script_running, check_scriptstop)
from kpf.calbench.IsCalSourceEnabled import IsCalSourceEnabled
from kpf.calbench.SetCalSource import SetCalSource
from kpf.calbench.SetND1 import SetND1
from kpf.calbench.SetND2 import SetND2
from kpf.calbench.WaitForCalSource import WaitForCalSource
from kpf.calbench.WaitForND1 import WaitForND1
from kpf.calbench.WaitForND2 import WaitForND2
from kpf.spectrograph.QueryFastReadMode import QueryFastReadMode
from kpf.spectrograph.SetObject import SetObject
from kpf.spectrograph.SetExpTime import SetExpTime
from kpf.spectrograph.SetProgram import SetProgram
from kpf.spectrograph.SetSourceSelectShutters import SetSourceSelectShutters
from kpf.spectrograph.SetTimedShutters import SetTimedShutters
from kpf.spectrograph.SetTriggeredDetectors import SetTriggeredDetectors
from kpf.spectrograph.StartAgitator import StartAgitator
from kpf.spectrograph.StartExposure import StartExposure
from kpf.spectrograph.StopAgitator import StopAgitator
from kpf.spectrograph.WaitForReady import WaitForReady
from kpf.spectrograph.WaitForReadout import WaitForReadout
from kpf.fiu.ConfigureFIU import ConfigureFIU
from kpf.fiu.WaitForConfigureFIU import WaitForConfigureFIU
from kpf.utils.ZeroOutSlewCalTime import ZeroOutSlewCalTime
from kpf.scripts.SetTargetInfo import SetTargetInfo


class ExecuteSlewCal(KPFScript):
    '''Script which executes the observations of a Slew Cal

    This must have arguments as input, either from a file using the `-f` command
    line tool, or passed in from the execution engine.

    ARGS:
    =====
    :OB: `dict` A fully specified slew cal observing block (OB).
    '''
    abortable = True

    @classmethod
    def pre_condition(cls, args, OB=None):
        pass

    @classmethod
    def perform(cls, args, OB=None):
        log.info('-------------------------')
        log.info(f"Running {cls.__name__}")
        log.info('-------------------------')

        progname = ktl.cache('kpfexpose', 'PROGNAME')
        original_progname = progname.read()

        kpfconfig = ktl.cache('kpfconfig')

        if len(OB.Calibrations) > 0:
            log.info(f'Executing Calibrations')
            ConfigureForCalibrations.execute(OB)
            log.info(f"Clearing stellar parameters")
            SetTargetInfo.execute({})
            SetProgram.execute({'progname': 'ENG'})
            for i,calibration in enumerate(OB.Calibrations):
                log.info(f'Executing Calibration {i+1}/{len(OB.Calibrations)}')
                ExecuteCal.execute(calibration.to_dict())
            log.info('Slew cal complete. Resetting SLEWCALREQ')
            kpfconfig['SLEWCALREQ'].write('No')
            log.info(f'Cleaning up after Calibrations')
            CleanupAfterCalibrations.execute(OB)
            # Restore Calsource to Simulcal source
            calsource = kpfconfig['SIMULCALSOURCE'].read()
            SetCalSource.execute({'CalSource': calsource, 'wait': True})
            # Restore progname
            log.info(f'Setting PROGNAME back to {original_progname}')
            SetProgram.execute({'progname': original_progname})

    @classmethod
    def post_condition(cls, args, OB=None):
        pass
