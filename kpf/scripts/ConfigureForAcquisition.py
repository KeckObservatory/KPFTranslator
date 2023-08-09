import os
from time import sleep
from packaging import version
from pathlib import Path
import yaml
import numpy as np

import ktl

from kpf.KPFTranslatorFunction import KPFTranslatorFunction
from kpf import (log, KPFException, FailedPreCondition, FailedPostCondition,
                 FailedToReachDestination, check_input)
from kpf.scripts import (register_script, obey_scriptrun, check_scriptstop,
                         add_script_log)
from kpf.scripts.ExecuteSlewCal import ExecuteSlewCal
from kpf.calbench.SetCalSource import SetCalSource
from kpf.guider.PredictGuiderParameters import PredictGuiderParameters
from kpf.guider.SetGuiderFPS import SetGuiderFPS
from kpf.guider.SetGuiderGain import SetGuiderGain
from kpf.fiu.InitializeTipTilt import InitializeTipTilt
from kpf.fiu.ConfigureFIU import ConfigureFIU
from kpf.utils.SetTargetInfo import SetTargetInfo


class ConfigureForAcquisition(KPFTranslatorFunction):
    '''Script which configures the instrument for Acquisition step.

    - Sets target parameters
    - Sets guide camera parameters
    - Sets FIU mode
    - Executes Slew Cal

    This must have arguments as input, either from a file using the `-f` command
    line tool, or passed in from the execution engine.

    Can be called by `ddoi_script_functions.configure_for_acquisition`.

    ARGS:
    =====
    None
    '''
    @classmethod
    @obey_scriptrun
    def pre_condition(cls, OB, logger, cfg):
        check_input(OB, 'Template_Name', allowed_values=['kpf_sci'])
        check_input(OB, 'Template_Version', version_check=True, value_min='0.5')
        # Check guider parameters
        guide_mode = OB.get('GuideMode', 'auto')
        if guide_mode == 'auto':
            check_input(OB, 'Jmag', allowed_types=[float, int])
        # Check Slewcals
        kpfconfig = ktl.cache('kpfconfig')
        if kpfconfig['SLEWCALREQ'].read(binary=True) is True:
            slewcal_argsfile = Path(kpfconfig['SLEWCALFILE'].read())
            if slewcal_argsfile.exists() is False:
                raise FailedPreCondition(f"Slew cal file {slewcal_argsfile} does not exist")

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

        kpfconfig = ktl.cache('kpfconfig')
        kpf_expmeter = ktl.cache('kpf_expmeter')

        # Set Octagon
        kpfconfig = ktl.cache('kpfconfig')
        calsource = kpfconfig['SIMULCALSOURCE'].read()
        octagon = ktl.cache('kpfcal', 'OCTAGON').read()
        log.debug(f"Current OCTAGON = {octagon}, desired = {calsource}")
        if octagon != calsource:
            log.info(f"Set CalSource/Octagon: {calsource}")
            SetCalSource.execute({'CalSource': calsource, 'wait': False})

        ## Execute Slew Cal if Requested
        if kpfconfig['SLEWCALREQ'].read(binary=True) is True:
            slewcal_argsfile = Path(kpfconfig['SLEWCALFILE'].read())
            log.info(f"Beginning Slew Cal")
            log.debug(f"Using: {slewcal_argsfile}")
            with open(slewcal_argsfile, 'r') as file:
                slewcal_args = yaml.safe_load(file)
            slewcal_args['TriggerCaHK'] = OB['TriggerCaHK']
            slewcal_args['TriggerGreen'] = OB['TriggerGreen']
            slewcal_args['TriggerRed'] = OB['TriggerRed']
            ExecuteSlewCal.execute(slewcal_args)
            log.info('Slew cal complete. Resetting SLEWCALREQ')
            kpfconfig['SLEWCALREQ'].write('No')
        else:
            # Set FIU Mode (this is done in ExecuteSlewCal if that is chosen)
            log.info('Setting FIU mode to Observing')
            ConfigureFIU.execute({'mode': 'Observing', 'wait': False})

        # Set Target Parameters from OB
        SetTargetInfo.execute(OB)

        # Set guide camera parameters (only manual supported for now)
        guide_mode = OB.get('GuideMode', 'auto')
        if guide_mode == 'manual':
            if OB.get('GuideCamGain', None) is not None:
                SetGuiderGain.execute(OB)
            if OB.get('GuideFPS', None) is not None:
                SetGuiderFPS.execute(OB)
        elif guide_mode == 'auto':
            guider_parameters = PredictGuiderParameters.execute(OB)
            SetGuiderGain.execute(guider_parameters)
            SetGuiderFPS.execute(guider_parameters)
        elif guide_mode == 'off':
            log.info(f"GuideMode is off, no guider parameters set")
        else:
            log.error(f"Guide mode '{guide_mode}' is not supported.")
            log.error(f"Not setting guider parameters.")

    @classmethod
    def post_condition(cls, OB, logger, cfg):
        pass
