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
from kpf.fiu.InitializeTipTilt import InitializeTipTilt
from kpf.fiu.ConfigureFIU import ConfigureFIU
from kpf.utils.SetTargetInfo import SetTargetInfo


class ConfigureForAcquisition(KPFTranslatorFunction):
    '''Script which configures the instrument for Acquisition step.

    - Sets target parameters
    - Sets FIU mode
    - Executes Slew Cal

    This must have arguments as input, either from a file using the `-f` command
    line tool, or passed in from the execution engine.

    ARGS:
    =====
    :OB: `dict` A fully specified science observing block (OB).
    '''
    @classmethod
    @obey_scriptrun
    def pre_condition(cls, OB, logger, cfg):
        check_input(OB, 'Template_Name', allowed_values=['kpf_sci'])
        check_input(OB, 'Template_Version', version_check=True, value_min='0.5')
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
                slewcal_OB = yaml.safe_load(file)
                slewcal_args = slewcal_OB.get('SEQ_Calibrations')[0]
                slewcal_args['Template_Name'] = 'kpf_slewcal'
                slewcal_args['Template_Version'] = '0.5'
            slewcal_args['TriggerCaHK'] = OB['TriggerCaHK']
            slewcal_args['TriggerGreen'] = OB['TriggerGreen']
            slewcal_args['TriggerRed'] = OB['TriggerRed']
            ExecuteSlewCal.execute(slewcal_args)
            log.info('Slew cal complete. Resetting SLEWCALREQ')
            kpfconfig['SLEWCALREQ'].write('No')
        # Set FIU Mode
        log.info('Setting FIU mode to Observing')
        ConfigureFIU.execute({'mode': 'Observing', 'wait': False})

        # Set Target Parameters from OB
        SetTargetInfo.execute(OB)

    @classmethod
    def post_condition(cls, OB, logger, cfg):
        pass
