import numpy as np

import ktl

from kpf.KPFTranslatorFunction import KPFTranslatorFunction
from kpf import (log, KPFException, FailedPreCondition, FailedPostCondition,
                 FailedToReachDestination, check_input)
from kpf.spectrograph.ResetDetectors import ResetDetectors


class WaitForReadout(KPFTranslatorFunction):
    '''Waits for the `kpfexpose.EXPOSE` keyword to be "Readout".  This will
    block until the camera enters the readout state.
    
    ARGS: None
    '''
    @classmethod
    def pre_condition(cls, args, logger, cfg):
        return True

    @classmethod
    def perform(cls, args, logger, cfg):
        kpfexpose = ktl.cache('kpfexpose')
        exptime = kpfexpose['EXPOSURE'].read(binary=True)

        detectors = kpfexpose['TRIG_TARG'].read()
        detector_list = detectors.split(',')

        starting_status = kpfexpose['EXPOSE'].read(binary=True)
        buffer_time = cfg.get('times', 'readout_buffer_time', fallback=10)
        wait_time = exptime+buffer_time if starting_status < 3 else buffer_time

        wait_logic = ''
        if 'Green' in detector_list:
            wait_logic += '(($kpfgreen.EXPSTATE == 4) or ($kpfgreen.EXPSTATE == 1))'
        if 'Red' in detector_list:
            if len(wait_logic) > 0: 
                wait_logic +=' and '
            wait_logic += '(($kpfred.EXPSTATE == 4) or ($kpfred.EXPSTATE == 1))'
        if 'Ca_HK' in detector_list:
            if len(wait_logic) > 0: 
                wait_logic +=' and '
            wait_logic += '(($kpf_hk.EXPSTATE == 4) or ($kpf_hk.EXPSTATE == 1))'
        if len(wait_logic) > 0: 
            wait_logic +=' and '
        wait_logic += '($kpfexpose.EXPOSE == 4)'
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
            log.debug(f'kpfexpose is {kpfexpose["EXPOSE"].read()}')
            log.debug(f'kpfexpose EXPLAINR = {kpfexpose["EXPLAINR"].read()}')
            errors = []
            if 'Red' in detector_list:
                kpfred = ktl.cache('kpfred')
                redexpstate = kpfred['EXPSTATE'].read()
                if redexpstate in ['Error', 'PowerOff']:
                    log.error(f"kpfred.EXPSTATE = {redexpstate}")
                    errors.append('Red')
            if 'Green' in detector_list:
                kpfgreen = ktl.cache('kpfgreen')
                greenexpstate = kpfgreen['EXPSTATE'].read()
                if greenexpstate in ['Error', 'PowerOff']:
                    log.error(f"kpfgreen.EXPSTATE = {greenexpstate}")
                    errors.append('Green')
            if len(errors) > 0:
                ResetDetectors.execute({})

    @classmethod
    def post_condition(cls, args, logger, cfg):
        kpfexpose = ktl.cache('kpfexpose')
        detectors = kpfexpose['TRIG_TARG'].read()
        detector_list = detectors.split(',')
        expose = kpfexpose['EXPOSE']
        status = expose.read()

        notok = [(status not in ['Readout', 'Ready'])]
        msg = f"Final detector state mismatch: {status} != Readout ("
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
            log.error(msg)
            return False
        return True
