from pathlib import Path
import numpy as np

import ktl

from kpf.KPFTranslatorFunction import KPFTranslatorFunction
from kpf import (log, KPFException, FailedPreCondition, FailedPostCondition,
                 FailedToReachDestination, check_input)
from kpf.spectrograph.ResetDetectors import *


class WaitForReady(KPFTranslatorFunction):
    '''Waits for the `kpfexpose.EXPOSE` keyword to be "Ready".  This will
    block until the camera is ready for another exposure.  Times out after
    waiting for exposure time plus a set buffer time.
    
    ARGS: None
    '''
    @classmethod
    def pre_condition(cls, args, logger, cfg):
        pass

    @classmethod
    def perform(cls, args, logger, cfg):
        kpfexpose = ktl.cache('kpfexpose')
        exptime = kpfexpose['EXPOSURE'].read(binary=True)
        starting_status = kpfexpose['EXPOSE'].read(binary=True)

        detectors = kpfexpose['TRIG_TARG'].read()
        detector_list = detectors.split(',')

        buffer_time = cfg.getfloat('times', 'readout_buffer_time', fallback=10)
        read_times = [cfg.getfloat('time_estimates', 'readout_red', fallback=60),
                      cfg.getfloat('time_estimates', 'readout_green', fallback=60),
                      cfg.getfloat('time_estimates', 'readout_cahk', fallback=1),
                      cfg.getfloat('time_estimates', 'readout_expmeter', fallback=1),
                      ]
        slowest_read = max(read_times)

        wait_time = exptime+slowest_read+buffer_time if starting_status < 3 else slowest_read+buffer_time

        wait_logic_steps = ['($kpfexpose.EXPOSE == 0)']
        if 'Green' in detector_list:
            wait_logic_steps.append("($kpfgreen.EXPSTATE == 0)")
        if 'Red' in detector_list:
            wait_logic_steps.append("($kpfred.EXPSTATE == 0)")
        if 'Ca_HK' in detector_list:
            wait_logic_steps.append("($kpf_hk.EXPSTATE == 0)")
        wait_logic = ' and '.join(wait_logic_steps)
        log.debug(f"Waiting ({wait_time:.0f}s max) for detectors to be ready")
        success = ktl.waitFor(wait_logic, timeout=wait_time)

        if success is True:
            log.debug(f'kpfexpose is {kpfexpose["EXPOSE"].read()}')
        else:
            log.warning('WaitForReady failed to reach expected state')
            log.debug(f'kpfexpose is {kpfexpose["EXPOSE"].read()}')
            log.debug(f'kpfexpose EXPLAINR = {kpfexpose["EXPLAINR"].read()}')
            log.debug(f'kpfexpose EXPLAINNR = {kpfexpose["EXPLAINNR"].read()}')
            ResetDetectors.execute({})

    @classmethod
    def post_condition(cls, args, logger, cfg):
        expr = "($kpfexpose.EXPOSE == 'Ready')"
        timeout = cfg.getfloat('times', 'kpfexpose_reset_time', fallback=10)
        ok = ktl.waitFor(expr, timeout=timeout)
        if ok is not True:
            expose = ktl.cache('kpfexpose', 'EXPOSE')
            raise FailedPostCondition(f"kpfexpose.EXPOSE={expose.read()} is not Ready")
