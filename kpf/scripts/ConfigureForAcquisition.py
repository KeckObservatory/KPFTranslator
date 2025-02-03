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
from kpf.calbench.SetCalSource import SetCalSource
from kpf.fiu.ConfigureFIU import ConfigureFIU
from kpf.scripts.SetTargetInfo import SetTargetInfo


class ConfigureForAcquisition(KPFScript):
    '''Script which configures the instrument for Acquisition step.

    - Sets target parameters
    - Sets FIU mode
    - Executes Slew Cal

    Args:
        OB (ObservingBlock): A valid observing block (OB).

    KTL Keywords Used:
    - `kpfconfig.SIMULCALSOURCE`

    Functions Called:
    - `kpf.calbench.SetCalSource`
    - `kpf.fiu.ConfigureFIU`
    - `kpf.scripts.SetTargetInfo`
    '''
    @classmethod
    def pre_condition(cls, args, OB=None):
        pass

    @classmethod
    def perform(cls, args, OB=None):
        if isinstance(OB, dict):
            OB = ObservingBlock(OB)
        log.info('-------------------------')
        log.info(f"Running {cls.__name__}")
        log.info('-------------------------')

        # Set Octagon
        calsource = ktl.cache('kpfconfig', 'SIMULCALSOURCE').read()
        octagon = ktl.cache('kpfcal', 'OCTAGON').read()
        log.debug(f"Current OCTAGON = {octagon}, desired = {calsource}")
        if octagon != calsource:
            log.info(f"Set CalSource/Octagon: {calsource}")
            SetCalSource.execute({'CalSource': calsource, 'wait': False})

        # Set FIU Mode
        log.info('Setting FIU mode to Observing')
        ConfigureFIU.execute({'mode': 'Observing', 'wait': False})

        # Set Target Parameters from OB
        SetTargetInfo.execute({}, OB=OB)

    @classmethod
    def post_condition(cls, args, OB=None):
        pass
