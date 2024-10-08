import os
import traceback
from time import sleep
from packaging import version
from pathlib import Path

import ktl

from kpf.KPFTranslatorFunction import KPFTranslatorFunction
from kpf import (log, KPFException, FailedPreCondition, FailedPostCondition,
                 FailedToReachDestination, check_input)
from kpf.scripts import (register_script, obey_scriptrun, check_scriptstop,
                         add_script_log)
from kpf.spectrograph.SetObject import SetObject
from kpf.spectrograph.SetExpTime import SetExpTime
from kpf.spectrograph.StartExposure import StartExposure
from kpf.spectrograph.WaitForL0File import WaitForL0File
from kpf.spectrograph.WaitForReady import WaitForReady
from kpf.spectrograph.WaitForReadout import WaitForReadout


class ExecuteDark(KPFTranslatorFunction):
    '''Script which executes a single Dark set in a calibration OB

    This must have arguments as input, either from a file using the `-f` command
    line tool, or passed in from the execution engine.

    ARGS:
    =====
    :args: `dict` An dark calibration component of an observing block (OB).
    '''
    abortable = True

    @classmethod
    def pre_condition(cls, args, logger, cfg):
        check_input(args, 'Template_Name', allowed_values=['kpf_dark'])
        check_input(args, 'Template_Version', version_check=True, value_min='0.5')

    @classmethod
    def perform(cls, args, logger, cfg):
        exposestatus = ktl.cache('kpfexpose', 'EXPOSE')
        # This is a time shim to insert a pause between exposures so that the
        # temperature of the CCDs can be measured by the archons
        archon_time_shim = cfg.getfloat('times', 'archon_temperature_time_shim',
                             fallback=2)

        check_scriptstop() # Stop here if requested

        # Wait for current exposure to readout
        if exposestatus.read() != 'Ready':
            log.info(f"Waiting for kpfexpose to be Ready")
            WaitForReady.execute({})
            log.info(f"Readout complete")
        check_scriptstop() # Stop here if requested
        log.info(f"Setting OBJECT: {args.get('Object')}")
        SetObject.execute(args)
        log.info(f"Set exposure time: {args.get('ExpTime'):.3f}")
        SetExpTime.execute(args)
        nexp = args.get('nExp', 1)
        exptime = float(args.get('ExpTime'))
        for j in range(nexp):
            check_scriptstop() # Stop here if requested
            # Wait for current exposure to readout
            if exposestatus.read() != 'Ready':
                log.info(f"Waiting for kpfexpose to be Ready")
                WaitForReady.execute({})
                log.info(f"Readout complete")
                if exptime < 2:
                    log.debug(f'Sleep {archon_time_shim:.1f}s for temperature reading')
                    sleep(archon_time_shim)
                check_scriptstop() # Stop here if requested
            # Start next exposure
            log.info(f"Starting exposure {j+1}/{nexp} ({args.get('Object')})")
            StartExposure.execute({})
            if exptime > 10:
                WaitForL0File.execute({})
            WaitForReadout.execute({})
            log.info(f"Readout has begun")

    @classmethod
    def post_condition(cls, args, logger, cfg):
        pass
