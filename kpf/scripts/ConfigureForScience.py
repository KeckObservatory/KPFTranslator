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
from kpf.calbench.SetSimulCalSource import SetSimulCalSource
from kpf.guider.ConfirmGuiding import ConfirmGuiding
from kpf.spectrograph.SetSourceSelectShutters import SetSourceSelectShutters
from kpf.spectrograph.SetTriggeredDetectors import SetTriggeredDetectors
from kpf.spectrograph.WaitForReady import WaitForReady
from kpf.telescope.EastNorth import EastNorth


class ConfigureForScience(KPFFunction):
    '''Script which configures the instrument for Science observations.

    - Sets octagon / simulcal source
    - Sets source select shutters
    - Set triggered detectors

    Args:
        observation (dict): A observation OB component in dictionary format (e.g.
                            using the output of the `.to_dict()` method of a
                            `kpf.ObservingBlocks.Observation.Observation` instance).

    KTL Keywords Used:

    - `kpfexpose.EXPOSE`

    Functions Called:

    - `kpf.calbench.SetSimulCalSource`
    - `kpf.guider.ConfirmGuiding`
    - `kpf.spectrograph.SetSourceSelectShutters`
    - `kpf.spectrograph.SetTriggeredDetectors`
    - `kpf.spectrograph.WaitForReady`
    - `kpf.telescope.EastNorth`
    '''
    @classmethod
    def pre_condition(cls, observation):
        pass

    @classmethod
    def perform(cls, observation):
        log.info('-------------------------')
        log.info(f"Running {cls.__name__}")
        log.info('-------------------------')

        # Offset if requested
#         NodN = observation.get('NodN', 0)
#         NodE = observation.get('NodE', 0)
#         if abs(NodN) > 0.01 or abs(NodE) > 0.01:
#             EastNorth.execute(observation)

        check_scriptstop()

        # Confirm guiding
        ConfirmGuiding.execute(observation)

        check_scriptstop()

        # Set Octagon
        SetSimulCalSource.execute({})

        check_scriptstop()

        # Set source select shutters
        exposestatus = ktl.cache('kpfexpose', 'EXPOSE')
        if exposestatus.read() != 'Ready':
            log.info(f"Waiting for kpfexpose to be Ready")
            WaitForReady.execute({})
            log.debug(f"kpfexpose is Ready")
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
