import os
import time
from packaging import version
from pathlib import Path
from datetime import datetime, timedelta
import numpy as np

import ktl

from kpf.KPFTranslatorFunction import KPFTranslatorFunction
from kpf import (log, KPFException, FailedPreCondition, FailedPostCondition,
                 FailedToReachDestination, check_input)
from kpf.scripts import (register_script, obey_scriptrun, check_scriptstop,
                         add_script_log)
from kpf.calbench.CalLampPower import CalLampPower
from kpf.calbench.SetCalSource import SetCalSource
from kpf.fiu.ConfigureFIU import ConfigureFIU
from kpf.fiu.VerifyCurrentBase import VerifyCurrentBase
from kpf.spectrograph.SetSourceSelectShutters import SetSourceSelectShutters
from kpf.spectrograph.SetTriggeredDetectors import SetTriggeredDetectors
from kpf.spectrograph.WaitForReady import WaitForReady


class ConfigureForScience(KPFTranslatorFunction):
    '''Script which configures the instrument for Science observations.

    - If needed, start tip tilt loops
    - Sets octagon / simulcal source
    - Sets source select shutters
    - Set triggered detectors

    This must have arguments as input, either from a file using the `-f` command
    line tool, or passed in from the execution engine.

    Can be called by `ddoi_script_functions.configure_for_science`.

    ARGS:
    =====
    None
    '''
    @classmethod
    @obey_scriptrun
    def pre_condition(cls, OB, logger, cfg):
        check_input(OB, 'Template_Name', allowed_values=['kpf_sci'])
        check_input(OB, 'Template_Version', version_check=True, value_min='0.5')
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

        check_scriptstop()

        # Check tip tilt loops
        requested_mode = OB.get('GuideMode', 'off')
        kpfguide = ktl.cache('kpfguide')
        all_loops = kpfguide['ALL_LOOPS'].read()
        tt_control = kpfguide['TIPTILT_CONTROL'].read()
        if (requested_mode in ['manual', 'auto'] and all_loops in ['Inactive', 'Mixed'])\
            or (requested_mode in ['off', 'telescope', False] and tt_control == 'Active'):
                log.error(f'OB requesting {requested_mode}, but guide loops '
                          f'are: {all_loops} ({tt_control})')
                # Check with user
                log.debug('Asking for user input')
                print()
                print("#####################################################")
                print("The tip tilt loops are not in the expected state based")
                print("on the information in the OB.")
                print()
                print("Do you wish to continue executing this OB")
                print("(Y/n)? ")
                print("#####################################################")
                print()
                user_input = input()
                log.debug(f'response: "{user_input}"')
                if user_input.lower().strip() in ['n', 'no', 'a', 'abort']:
                    raise KPFException("User chose to halt execution")

        check_scriptstop()

        if requested_mode in ['manual', 'auto']:
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
                print("Do you wish to continue executing this OB")
                print("(Y/n)? ")
                print("#####################################################")
                print()
                user_input = input()
                log.debug(f'response: "{user_input}"')
                if user_input.lower().strip() in ['n', 'no', 'a', 'abort']:
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
        OB['TriggerGuide'] = (OB.get('GuideMode', 'off') != 'off')
        SetTriggeredDetectors.execute(OB)

        check_scriptstop()

    @classmethod
    def post_condition(cls, OB, logger, cfg):
        pass
