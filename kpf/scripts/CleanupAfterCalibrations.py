import os
from time import sleep
from packaging import version
from pathlib import Path
import numpy as np

import ktl

from kpf.KPFTranslatorFunction import KPFTranslatorFunction
from kpf import (log, KPFException, FailedPreCondition, FailedPostCondition,
                 FailedToReachDestination, check_input)
from kpf.scripts import (register_script, obey_scriptrun, check_scriptstop,
                         add_script_log)
from kpf.calbench.CalLampPower import CalLampPower
from kpf.calbench.IsCalSourceEnabled import IsCalSourceEnabled
from kpf.fiu.ConfigureFIU import ConfigureFIU
from kpf.spectrograph.SetObject import SetObject
from kpf.spectrograph.StopAgitator import StopAgitator
from kpf.spectrograph.WaitForReady import WaitForReady
from kpf.utils.SetTargetInfo import SetTargetInfo


class CleanupAfterCalibrations(KPFTranslatorFunction):
    '''Script which cleans up after Cal OBs.

    This must have arguments as input, either from a file using the `-f` command
    line tool, or passed in from the execution engine.

    Can be called by `ddoi_script_functions.post_observation_cleanup`.

    ARGS:
    =====
    None
    '''
    @classmethod
    @obey_scriptrun
    def pre_condition(cls, OB, logger, cfg):
        check_input(OB, 'Template_Name', allowed_values=['kpf_cal'])
        check_input(OB, 'Template_Version', version_check=True, value_min='0.3')

    @classmethod
    def perform(cls, OB, logger, cfg):
        log.info('-------------------------')
        log.info(f"Running {cls.__name__}")
        for key in OB:
            if key not in ['SEQ_Darks', 'SEQ_Calibrations']:
                log.debug(f"  {key}: {OB[key]}")
            else:
                log.debug(f"  {key}:")
                for entry in OB[key]:
                    log.debug(f"    {entry}")
        log.info('-------------------------')

        # Power off lamps
        if OB.get('leave_lamps_on', False) == True:
            log.info('Not turning lamps off because command line option was invoked')
        else:
            sequence = OB.get('SEQ_Calibrations', None)
            lamps = set([x['CalSource'] for x in sequence if x['CalSource'] != 'Home'])\
                    if sequence is not None else []
            for lamp in lamps:
                if IsCalSourceEnabled.execute({'CalSource': lamp}) == True:
                    if lamp in ['Th_daily', 'Th_gold', 'U_daily', 'U_gold',
                                'BrdbandFiber', 'WideFlat']:
                        CalLampPower.execute({'lamp': lamp, 'power': 'off'})

        kpfconfig = ktl.cache('kpfconfig')
        runagitator = kpfconfig['USEAGITATOR'].read(binary=True)
        if runagitator is True:
            StopAgitator.execute({})

        log.info(f"Stowing FIU")
        ConfigureFIU.execute({'mode': 'Stowed'})

        # Set OBJECT back to empty string
        log.info('Waiting for readout to finish')
        WaitForReady.execute({})
        SetObject.execute({'Object': ''})

        # Clear target info
        SetTargetInfo.execute({})

    @classmethod
    def post_condition(cls, OB, logger, cfg):
        pass

    @classmethod
    def add_cmdline_args(cls, parser, cfg=None):
        parser.add_argument('--leave_lamps_on', dest="leave_lamps_on",
                            default=False, action="store_true",
                            help='Leave the lamps on after cleanup phase?')
        return super().add_cmdline_args(parser, cfg)
