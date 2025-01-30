import numpy as np

import ktl

from kpf import log, cfg, check_input
from kpf.exceptions import *
from kpf.KPFTranslatorFunction import KPFFunction, KPFScript
from kpf.spectrograph.ResetDetectors import *


class WaitForReadout(KPFFunction):
    '''Waits for the `kpfexpose.EXPOSE` keyword to be "Readout".  This will
    block until the camera enters the readout state.
    
    ARGS:
    =====
    None
    '''
    @classmethod
    def pre_condition(cls, args):
        pass

    @classmethod
    def perform(cls, args):
        kpfexpose = ktl.cache('kpfexpose')
        exptime = kpfexpose['EXPOSURE'].read(binary=True)
        starting_status = kpfexpose['EXPOSE'].read(binary=True)

        detectors = kpfexpose['TRIG_TARG'].read()
        detector_list = detectors.split(',')

        buffer_time = cfg.getfloat('times', 'readout_buffer_time', fallback=10)
        wait_time = exptime+buffer_time if starting_status < 3 else buffer_time

        wait_logic_steps = ['($kpfexpose.EXPOSE == 4)']
        if 'Green' in detector_list:
            wait_logic_steps.append("($kpfgreen.EXPSTATE == 4)")
        if 'Red' in detector_list:
            wait_logic_steps.append("($kpfred.EXPSTATE == 4)")
        if 'Ca_HK' in detector_list:
            wait_logic_steps.append("($kpf_hk.EXPSTATE == 4)")
        wait_logic = ' and '.join(wait_logic_steps)

        log.debug(f"Waiting ({wait_time:.0f}s max) for readout to begin")
        success = ktl.waitFor(wait_logic, timeout=wait_time)
        if success is True:
            log.debug(f'kpfexpose is {kpfexpose["EXPOSE"].read()}')
            if 'Green' in detector_list:
                nextfile = ktl.cache('kpfgreen', 'NEXTFILE')
                log.debug(f"Green nextfile: {nextfile.read()}")
            if 'Red' in detector_list:
                nextfile = ktl.cache('kpfred', 'NEXTFILE')
                log.debug(f"Red nextfile: {nextfile.read()}")
        else:
            log.warning('WaitForReadout failed to reach expected state')
            log.debug(f'kpfexpose is {kpfexpose["EXPOSE"].read()}')
            log.debug(f'kpfexpose EXPLAINR = {kpfexpose["EXPLAINR"].read()}')
            log.debug(f'kpfexpose EXPLAINNR = {kpfexpose["EXPLAINNR"].read()}')
            RecoverDetectors.execute({})

    @classmethod
    def post_condition(cls, args):
        expr = "($kpfexpose.EXPOSE == 'Ready') or ($kpfexpose.EXPOSE == 'Readout')"
        timeout = cfg.getfloat('times', 'kpfexpose_reset_time', fallback=10)
        ok = ktl.waitFor(expr, timeout=timeout)
        if ok is not True:
            expose = ktl.cache('kpfexpose', 'EXPOSE')
            raise FailedPostCondition(f"kpfexpose.EXPOSE={expose.read()} is not Ready or Readout")
