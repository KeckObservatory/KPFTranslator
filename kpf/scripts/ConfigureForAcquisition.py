import os
from time import sleep
from packaging import version
from pathlib import Path
import yaml

import ktl

from kpf import log, cfg, check_input
from kpf.exceptions import *
from kpf.KPFTranslatorFunction import KPFFunction, KPFScript
from kpf.scripts import register_script, check_scriptstop, add_script_log
from kpf.ObservingBlocks.ObservingBlock import ObservingBlock
from kpf.scripts.ExecuteSlewCal import ExecuteSlewCal
from kpf.calbench.SetCalSource import SetCalSource
from kpf.fiu.InitializeTipTilt import InitializeTipTilt
from kpf.fiu.ConfigureFIU import ConfigureFIU
from kpf.scripts.SetTargetInfo import SetTargetInfo


class ConfigureForAcquisition(KPFScript):
    '''Script which configures the instrument for Acquisition step.

    - Sets target parameters
    - Sets FIU mode
    - Executes Slew Cal

    ARGS:
    =====
    :OB: `dict` A fully specified science observing block (OB).
    '''
    @classmethod
    def pre_condition(cls, args, OB=None):
        # Check Slewcals
        kpfconfig = ktl.cache('kpfconfig')
        if kpfconfig['SLEWCALREQ'].read(binary=True) is True:
            slewcal_argsfile = Path(kpfconfig['SLEWCALFILE'].read())
            if slewcal_argsfile.exists() is False:
                raise FailedPreCondition(f"Slew cal file {slewcal_argsfile} does not exist")

    @classmethod
    def perform(cls, args, OB=None):
        if isinstance(OB, dict):
            OB = ObservingBlock(OB)
        log.info('-------------------------')
        log.info(f"Running {cls.__name__}")
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
            log.debug(f"Using: {slewcal_argsfile}")
            with open(slewcal_argsfile, 'r') as file:
                slewcal_OBdict = yaml.safe_load(file)
                slewcal_OB = ObservingBlock(slewcal_OBdict)
            ExecuteSlewCal.execute({}, OB=slewcal_OB)
        # Set FIU Mode
        log.info('Setting FIU mode to Observing')
        ConfigureFIU.execute({'mode': 'Observing', 'wait': False})

        # Set Target Parameters from OB
        SetTargetInfo.execute(OB)

    @classmethod
    def post_condition(cls, args, OB=None):
        pass
