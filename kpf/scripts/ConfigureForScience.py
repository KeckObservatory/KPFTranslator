import os
from time import sleep
from packaging import version
from pathlib import Path
import yaml
import numpy as np

import ktl

from ddoitranslatormodule.KPFTranslatorFunction import KPFTranslatorFunction
from .. import (log, KPFException, FailedPreCondition, FailedPostCondition,
                FailedToReachDestination, check_input)
from . import register_script, obey_scriptrun, check_scriptstop
from ..calbench.CalLampPower import CalLampPower
from ..calbench.SetCalSource import SetCalSource
from ..fiu.ConfigureFIU import ConfigureFIU
# from ..fiu.SetADCAngles import SetADCAngles
from ..spectrograph.SetSourceSelectShutters import SetSourceSelectShutters
from ..spectrograph.SetTriggeredDetectors import SetTriggeredDetectors
from ..spectrograph.WaitForReady import WaitForReady
from ..expmeter.SetExpMeterExptime import SetExpMeterExptime


class ConfigureForScience(KPFTranslatorFunction):
    '''Script which configures the instrument for Science observations.
    
    - Turns on lamp power for all sequences
    - Sets octagon / simulcal source & ND filters for first sequence (skip if
      slew cal is selected?)
    - Sets source select shutters

    Can be called by `ddoi_script_functions.configure_for_science`.
    '''
    @classmethod
    @obey_scriptrun
    def pre_condition(cls, OB, logger, cfg):
        check_input(OB, 'Template_Name', allowed_values=['kpf_sci'])
        check_input(OB, 'Template_Version', version_check=True, value_min='0.3')
        return True

    @classmethod
    def perform(cls, OB, logger, cfg):
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

        # Turn on lamps
        lamps = [seq['CalSource'] for seq in OB.get('SEQ_Observations')\
                 if 'CalSource' in seq.keys()]
#         for lamp in set(lamps):
#             if lamp in ['Th_daily', 'Th_gold', 'U_daily', 'U_gold',
#                         'BrdbandFiber', 'WideFlat']:
#                 log.debug(f"Ensuring lamp {lamp} is on")
#                 CalLampPower.execute({'lamp': lamp, 'power': 'on'})

        # 

        # Set Octagon
        log.info(f"Set CalSource/Octagon: {lamps[0]}")
        SetCalSource.execute({'CalSource': lamps[0], 'wait': False})

        # Set source select shutters
        WaitForReady.execute({})
        log.info(f"Set Source Select Shutters")
        SetSourceSelectShutters.execute({'SSS_Science': True,
                                         'SSS_Sky': True,
                                         'SSS_SoCalSci': False,
                                         'SSS_SoCalCal': False,
                                         'SSS_CalSciSky': False})

    @classmethod
    def post_condition(cls, OB, logger, cfg):
        return True
