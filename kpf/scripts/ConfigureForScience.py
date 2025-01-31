import os
import time
from packaging import version
from pathlib import Path
from datetime import datetime, timedelta
import numpy as np

import ktl

from kpf import log, cfg, check_input
from kpf.exceptions import *
from kpf.KPFTranslatorFunction import KPFFunction, KPFScript
from kpf.scripts import (register_script, obey_scriptrun, check_scriptstop,
                         add_script_log)
from kpf.calbench.CalLampPower import CalLampPower
from kpf.calbench.SetCalSource import SetCalSource
from kpf.fiu.ConfigureFIU import ConfigureFIU
from kpf.fiu.VerifyCurrentBase import VerifyCurrentBase
from kpf.spectrograph.SetSourceSelectShutters import SetSourceSelectShutters
from kpf.spectrograph.SetTriggeredDetectors import SetTriggeredDetectors
from kpf.spectrograph.WaitForReady import WaitForReady


class ConfigureForScience(KPFScript):
    '''Script which configures the instrument for Science observations.

    - Sets octagon / simulcal source
    - Sets source select shutters
    - Set triggered detectors

    This must have arguments as input, either from a file using the `-f` command
    line tool, or passed in from the execution engine.

    Can be called by `ddoi_script_functions.configure_for_science`.

    ARGS:
    =====
    :OB: `dict` A fully specified science observing block (OB).
    '''
    @classmethod
    @obey_scriptrun
    def pre_condition(cls, args, OB=None):
        pass

    @classmethod
    def perform(cls, args, OB=None):
        if isinstance(OB, dict):
            OB = ObservingBlock(OB)
        log.info('-------------------------')
        log.info(f"Running {cls.__name__}")
        for key in OB:
            if key not in ['SEQ_Observations']:
                log.debug(f"  {key}: {OB[key]}")
            else:
                log.debug(f"  {key}:")
                for entry in OB[key]:
                    log.debug(f"    {entry}")
        log.info('-------------------------')

        check_scriptstop()

        matched_PO = VerifyCurrentBase.execute({})
        if matched_PO == False:
            # Check with user
            log.debug('Asking for user input')
            print()
            print("#####################################################")
            print("The dcs.PONAME value is incosistent with CURRENT_BASE")
            print("Please double check that the target object is where you")
            print("want it to be before proceeding.")
            print()
            print("Do you wish to continue executing this OB?")
            print("(y/n) [y]:")
            print("#####################################################")
            print()
            user_input = input()
            log.debug(f'response: "{user_input}"')
            if user_input.lower().strip() in ['n', 'no', 'a', 'abort', 'q', 'quit']:
                raise KPFException("User chose to halt execution")

        check_scriptstop()

        # Set Octagon
        kpfconfig = ktl.cache('kpfconfig')
        calsource = kpfconfig['SIMULCALSOURCE'].read()
        octagon = ktl.cache('kpfcal', 'OCTAGON').read()
        log.debug(f"Current OCTAGON = {octagon}, desired = {calsource}")
        if octagon != calsource:
            log.info(f"Set CalSource/Octagon: {calsource}")
            SetCalSource.execute({'CalSource': calsource, 'wait': False})

        check_scriptstop()

        exposestatus = ktl.cache('kpfexpose', 'EXPOSE')
        if exposestatus.read() != 'Ready':
            log.info(f"Waiting for kpfexpose to be Ready")
            WaitForReady.execute({})
            log.debug(f"kpfexpose is Ready")
        # Set source select shutters
        log.info(f"Set Source Select Shutters")
        SetSourceSelectShutters.execute({'SSS_Science': True,
                                         'SSS_Sky': not OB.get('BlockSky', False),
                                         'SSS_SoCalSci': False,
                                         'SSS_SoCalCal': False,
                                         'SSS_CalSciSky': False})

        # Set Triggered Detectors
        OB['TriggerGuide'] = True
        SetTriggeredDetectors.execute(OB)

        check_scriptstop()

    @classmethod
    def post_condition(cls, args, OB=None):
        pass
