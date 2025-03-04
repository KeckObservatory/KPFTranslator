import os
import time
from packaging import version
from pathlib import Path
from datetime import datetime, timedelta
import numpy as np

import ktl

from kpf import log, cfg
from kpf.exceptions import *
from kpf.KPFTranslatorFunction import KPFFunction, KPFScript
from kpf.scripts import register_script, check_scriptstop, add_script_log
from kpf.calbench.CalLampPower import CalLampPower
from kpf.calbench.SetCalSource import SetCalSource
from kpf.calbench.SetSimulCalSource import SetSimulCalSource
from kpf.fiu.ConfigureFIU import ConfigureFIU
from kpf.fiu.VerifyCurrentBase import VerifyCurrentBase
from kpf.spectrograph.SetSourceSelectShutters import SetSourceSelectShutters
from kpf.spectrograph.SetTriggeredDetectors import SetTriggeredDetectors
from kpf.spectrograph.WaitForReady import WaitForReady


class ConfigureForScience(KPFFunction):
    '''Script which configures the instrument for Science observations.

    - Sets octagon / simulcal source
    - Sets source select shutters
    - Set triggered detectors

    ARGS:
    =====

    '''
    @classmethod
    def pre_condition(cls, observation):
        pass

    @classmethod
    def perform(cls, observation):
        log.info('-------------------------')
        log.info(f"Running {cls.__name__}")
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

        # Set Octagon
        SetSimulCalSource.execute({})

        check_scriptstop()

        exposestatus = ktl.cache('kpfexpose', 'EXPOSE')
        if exposestatus.read() != 'Ready':
            log.info(f"Waiting for kpfexpose to be Ready")
            WaitForReady.execute({})
            log.debug(f"kpfexpose is Ready")
        # Set source select shutters
        log.info(f"Set Source Select Shutters")
        SetSourceSelectShutters.execute({'OpenScienceShutter': True,
                                         'OpenSkyShutter': not observation.get('BlockSky', False),
                                         'OpenSoCalSciShutter': False,
                                         'OpenSoCalCalShutter': False,
                                         'OpenCalSciSkyShutter': False})

        # Set Triggered Detectors
        observation['TriggerGuide'] = True
        SetTriggeredDetectors.execute(observation)

        check_scriptstop()

    @classmethod
    def post_condition(cls, observation):
        pass
