import sys
import time
import os
import traceback
from pathlib import Path
import yaml

import ktl

from kpf import log, cfg
from kpf.exceptions import *
from kpf.KPFTranslatorFunction import KPFFunction, KPFScript
from kpf.scripts import (check_script_running, set_script_keywords,
                         add_script_log, wait_for_script, clear_script_keywords)
from kpf.ObservingBlocks.ObservingBlock import ObservingBlock
from kpf.ObservingBlocks.SubmitExecutionHistory import SubmitExecutionHistory
from kpf.fiu.VerifyCurrentBase import VerifyCurrentBase
from kpf.scripts.SendTargetToMagiq import SendTargetToMagiq
from kpf.scripts.ConfigureForCalibrations import ConfigureForCalibrations
from kpf.scripts.ExecuteCal import ExecuteCal
from kpf.scripts.CleanupAfterCalibrations import CleanupAfterCalibrations
from kpf.scripts.ConfigureForAcquisition import ConfigureForAcquisition
from kpf.scripts.WaitForConfigureAcquisition import WaitForConfigureAcquisition
from kpf.scripts.ConfigureForScience import ConfigureForScience
from kpf.scripts.WaitForConfigureScience import WaitForConfigureScience
from kpf.scripts.ExecuteSci import ExecuteSci
from kpf.scripts.CleanupAfterScience import CleanupAfterScience
from kpf.spectrograph.SetProgram import SetProgram
from kpf.utils.GetScheduledProgram import GetScheduledProgram


class RunOB(KPFScript):
    '''Script to run an OB.

    ARGS:
    =====
    * __leave_lamps_on__ - `bool` Leave calibration lamps on when done?
    * __OB__ - `ObservingBlock` or `dict` A valid observing block (OB).
    '''
    @classmethod
    def pre_condition(cls, args, OB=None):
        # If specified obey the ALLOWSCHEDULEDCALS keyword
        if args.get('scheduled', False) == True:
            ALLOWSCHEDULEDCALS = ktl.cache('kpfconfig', 'ALLOWSCHEDULEDCALS')
            if ALLOWSCHEDULEDCALS.read(binary=True) == False:
                raise FailedPreCondition('ALLOWSCHEDULEDCALS is No')
        # Read the OB
        if isinstance(OB, dict):
            OB = ObservingBlock(OB)
        elif isinstance(OB, ObservingBlock):
            pass
        else:
            raise FailedPreCondition('Input must be dict or ObservingBlock')
        # Validate the OB
        OB.validate()
        # Check for script running unless waitforscript is set
        if args.get('waitforscript', False) is False:
            check_script_running()

    @classmethod
    @add_script_log(Path(__file__).name.replace(".py", ""))
    def perform(cls, args, OB=None):
        # If requested wait for an existing script to complete
        if args.get('waitforscript', False) == True:
            newscript = f'{Path(__file__).name.replace(".py", "")}(PID {os.getpid()})'
            wait_for_script(newscript=newscript)
        set_script_keywords(Path(__file__).name, os.getpid())

        log.info('-------------------------')
        log.info(f"Running {cls.__name__}")
        log.info('-------------------------')
        if isinstance(OB, dict):
            OB = ObservingBlock(OB)
        if OB.OBID not in [None, '']:
            log.info(f"OB ID = {OB.OBID}")

        # Send Target info to Magiq for OA
        if OB.Target is not None:
            SendTargetToMagiq.execute({})

        # Add slew cal to OB if keywords indicate one is requested
        kpfconfig = ktl.cache('kpfconfig')
        if len(OB.Observations) > 0 and kpfconfig['SLEWCALREQ'].read(binary=True) is True:
            slewcal_OBfile = Path(kpfconfig['SLEWCALFILE'].read())
            log.info('Slewcal has been requested')
            log.debug(f"Reading: {slewcal_OBfile}")
            with open(slewcal_OBfile, 'r') as file:
                slewcal_OBdict = yaml.safe_load(file)
                slewcal_OB = ObservingBlock(slewcal_OBdict)
            OB.Calibrations.extend(slewcal_OB.Calibrations)
            # Now that slewcal has been added, reset the SLEWCALREQ value
            kpfconfig['SLEWCALREQ'].write(False)

        # Execute calibrations
        if len(OB.Calibrations) > 0:
            log.info(f'Executing Calibrations')
            if len(OB.Observations) > 0:
                kpfconfig['SCRIPTMSG'].write('Executing Slew Cal')
            ConfigureForCalibrations.execute(args, OB=OB)
            for i,calibration in enumerate(OB.Calibrations):
                log.info(f'Executing Calibration {i+1}/{len(OB.Calibrations)}')
                ExecuteCal.execute(calibration.to_dict())
            log.info(f'Cleaning up after Calibrations')
            CleanupAfterCalibrations.execute(args, OB=OB)
            if len(OB.Observations) > 0:
                kpfconfig['SCRIPTMSG'].write('Slew Cal complete. Setting FIU to observing mode')

        # Configure for Acquisition
        if OB.Target is not None:
            log.info(f'Configuring for Acquisition')
            try:
                ConfigureForAcquisition.execute(args, OB=OB)
            except Exception as e:
                log.error(e)
                CleanupAfterScience.execute(args, OB=OB)
                return
            WaitForConfigureAcquisition.execute(args, OB=OB)

        # Execute science observations
        if len(OB.Observations) > 0:
            log.info(f'Configuring for Observations')
            VerifyCurrentBase.execute({'query_user': True})
            for i,observation in enumerate(OB.Observations):
                observation_dict = observation.to_dict()
                observation_dict['Gmag'] = OB.Target.get('Gmag')
                ConfigureForScience.execute(observation_dict)
                if OB.ProgramID != '':
                    SetProgram.execute('progname': OB.ProgramID)
                else:
                    program = GetScheduledProgram.execute({})
                    SetProgram.execute('progname': program)
                WaitForConfigureScience.execute(observation_dict)
                log.info(f'Executing Observation {i+1}/{len(OB.Observations)}')
                ExecuteSci.execute(observation_dict)
            log.info(f'Cleaning up after Observations')
            CleanupAfterScience.execute(args, OB=OB)

        if OB.OBID != '':
            SubmitExecutionHistory.execute({'id': OB.OBID})

        clear_script_keywords()

    @classmethod
    def post_condition(cls, args, OB=None):
        pass

    @classmethod
    def add_cmdline_args(cls, parser):
        parser.add_argument('--leave_lamps_on', dest="leave_lamps_on",
            default=False, action="store_true",
            help='Leave the calibration lamps on after cleanup phase?')
        parser.add_argument('--waitforscript', dest="waitforscript",
            default=False, action="store_true",
            help='Wait for running script to end before starting?')
        parser.add_argument('--scheduled', dest="scheduled",
            default=False, action="store_true",
            help='Script is scheduled and should obey ALLOWSCHEDULEDCALS keyword')
        return super().add_cmdline_args(parser)
