from pathlib import Path
import numpy as np

import ktl

from kpf.KPFTranslatorFunction import KPFTranslatorFunction
from kpf import (log, KPFException, FailedPreCondition, FailedPostCondition,
                 FailedToReachDestination, check_input)
from kpf.spectrograph import ResetDetectors


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

        detectors = kpfexpose['TRIG_TARG'].read()
        detector_list = detectors.split(',')

        starting_status = kpfexpose['EXPOSE'].read(binary=True)

        buffer_time = cfg.getfloat('times', 'readout_buffer_time', fallback=10)
        slowest_read = cfg.getfloat('times', 'slowest_readout_time', fallback=120)

        wait_time = exptime+slowest_read+buffer_time if starting_status < 3 else slowest_read+buffer_time

        wait_logic = ''
        if 'Green' in detector_list:
            wait_logic += '(($kpfgreen.EXPSTATE == 0) or ($kpfgreen.EXPSTATE == 1))'
        if 'Red' in detector_list:
            if len(wait_logic) > 0: 
                wait_logic +=' and '
            wait_logic += '(($kpfred.EXPSTATE == 0) or ($kpfred.EXPSTATE == 1))'
        if 'Ca_HK' in detector_list:
            if len(wait_logic) > 0: 
                wait_logic +=' and '
            wait_logic += '(($kpf_hk.EXPSTATE == 0) or ($kpf_hk.EXPSTATE == 1))'
        if len(wait_logic) > 0: 
            wait_logic +=' and '
        wait_logic += '($kpfexpose.EXPOSE == 0)'
        log.debug(f"Waiting ({wait_time:.0f}s max) for detectors to be ready")
        success = ktl.waitFor(wait_logic, timeout=wait_time)

        if success is True:
            log.debug(f'kpfexpose is {kpfexpose["EXPOSE"].read()}')
        else:
            log.warning('WaitForReady failed to reach expected state')
            log.debug(f'kpfexpose is {kpfexpose["EXPOSE"].read()}')
            log.debug(f'kpfexpose EXPLAINR = {kpfexpose["EXPLAINR"].read()}')
            log.debug(f'kpfexpose EXPLAINNR = {kpfexpose["EXPLAINNR"].read()}')
            if 'Red' in detector_list:
                kpfred = ktl.cache('kpfred')
                redexpstate = kpfred['EXPSTATE'].read()
                if redexpstate in ['Error', 'PowerOff', 'Readout']:
                    log.error(f"kpfred.EXPSTATE = {redexpstate}")
                    ResetDetectors.ResetRedDetector.execute({})
            if 'Green' in detector_list:
                kpfgreen = ktl.cache('kpfgreen')
                greenexpstate = kpfgreen['EXPSTATE'].read()
                if greenexpstate in ['Error', 'PowerOff', 'Readout']:
                    log.error(f"kpfgreen.EXPSTATE = {greenexpstate}")
                    ResetDetectors.ResetGreenDetector.execute({})
            if 'Ca_HK' in detector_list:
                kpf_hk = ktl.cache('kpf_hk')
                hkexpstate = kpf_hk['EXPSTATE'].read()
                if hkexpstate != 'Ready':
                    log.error(f"kpf_hk.EXPSTATE = {hkexpstate}")
                    ResetDetectors.ResetCaHKDetector.execute({})

    @classmethod
    def post_condition(cls, args, logger, cfg):
        kpfexpose = ktl.cache('kpfexpose')
        detectors = kpfexpose['TRIG_TARG'].read()
        detector_list = detectors.split(',')
        expose = kpfexpose['EXPOSE']
        status = expose.read()

        notok = [(status != 'Ready')]
        msg = f"Final detector state mismatch: {status} != Ready ("
        if 'Green' in detector_list:
            greenexpstate = ktl.cache('kpfgreen', 'EXPSTATE').read()
            notok.append(greenexpstate == 'Error')
            msg += f"kpfgreen.EXPSTATE = {greenexpstate} "
        if 'Red' in detector_list:
            redexpstate = ktl.cache('kpfred', 'EXPSTATE').read()
            notok.append(redexpstate == 'Error')
            msg += f"kpfred.EXPSTATE = {redexpstate} "
        if 'Ca_HK' in detector_list:
            cahkexpstate = ktl.cache('kpf_hk', 'EXPSTATE').read()
            notok.append(cahkexpstate == 'Error')
            msg += f"kpf_hk.EXPSTATE = {cahkexpstate} "
        msg += ')'
        notok = np.array(notok)

        if np.any(notok):
            raise FailedPostCondition(msg)
