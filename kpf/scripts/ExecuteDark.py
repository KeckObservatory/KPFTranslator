import os
from time import sleep
from packaging import version
from pathlib import Path

import ktl

from ddoitranslatormodule.KPFTranslatorFunction import KPFTranslatorFunction
from .. import (log, KPFException, FailedPreCondition, FailedPostCondition,
                FailedToReachDestination, check_input)
from . import register_script, obey_scriptrun, check_scriptstop, add_script_log
from ..spectrograph.SetObject import SetObject
from ..spectrograph.SetExptime import SetExptime
from ..spectrograph.StartExposure import StartExposure
from ..spectrograph.WaitForReady import WaitForReady
from ..spectrograph.WaitForReadout import WaitForReadout


class ExecuteDark(KPFTranslatorFunction):
    '''Script which executes a single Dark set in a calibration OB
    
    Can be called by `ddoi_script_functions.execute_observation`.
    '''
    abortable = True

    @classmethod
    def abort_execution(args, logger, cfg):
        scriptstop = ktl.cache('kpfconfig', 'SCRIPTSTOP')
        log.warning('Abort recieved, setting kpfconfig.SCRTIPSTOP=Yes')
        scriptstop.write('Yes')

    @classmethod
    def pre_condition(cls, args, logger, cfg):
        check_input(args, 'Template_Name', allowed_values=['kpf_dark'])
        check_input(args, 'Template_Version', version_check=True, value_min='0.5')
        return True

    @classmethod
    def perform(cls, args, logger, cfg):
        exposestatus = ktl.cache('kpfexpose', 'EXPOSE')
        # This is a time shim to insert a pause between exposures so that the
        # temperature of the CCDs can be measured by the archons
        archon_time_shim = cfg.get('times', 'archon_temperature_time_shim',
                             fallback=2)

        # Wait for current exposure to readout
        if exposestatus.read() != 'Ready':
            log.info(f"Waiting for kpfexpose to be Ready")
            WaitForReady.execute({})
            log.info(f"Readout complete")
            sleep(archon_time_shim)
        check_scriptstop() # Stop here if requested
        log.info(f"Setting OBJECT: {args.get('Object')}")
        SetObject.execute(args)
        log.info(f"Set exposure time: {args.get('Exptime'):.3f}")
        SetExptime.execute(args)
        nexp = args.get('nExp', 1)
        for j in range(nexp):
            check_scriptstop() # Stop here if requested
            # Wait for current exposure to readout
            if exposestatus.read() != 'Ready':
                log.info(f"Waiting for kpfexpose to be Ready")
                WaitForReady.execute({})
                log.info(f"Readout complete")
                sleep(archon_time_shim)
                check_scriptstop() # Stop here if requested
            # Start next exposure
            log.info(f"Starting exposure {j+1}/{nexp} ({args.get('Object')})")
            StartExposure.execute({})
            WaitForReadout.execute({})
            log.info(f"Readout has begun")

    @classmethod
    def post_condition(cls, args, logger, cfg):
        return True
