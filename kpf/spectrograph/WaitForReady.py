import numpy as np

import ktl

from ddoitranslatormodule.KPFTranslatorFunction import KPFTranslatorFunction


class WaitForReady(KPFTranslatorFunction):
    '''Waits for the `kpfexpose.EXPOSE` keyword to be "Ready".  This will
    block until the camera is ready for another exposure.  Times out after
    waiting for exposure time plus a set buffer time.
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

        cfg = cls._load_config(cls, cfg)
        buffer_time = cfg.get('times', 'readout_buffer_time', fallback=10)
        slowest_read = cfg.get('times', 'slowest_readout_time', fallback=120)

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
#         print(f"  Wait Logic: {wait_logic}")
        print(f"  Waiting ({wait_time:.0f}s max) for detectors to be ready")
        success = ktl.waitFor(wait_logic, timeout=wait_time)
        if success is True:
            if 'Green' in detector_list:
                lastfile = ktl.cache('kpfgreen', 'FITSFILE')
                print(f"  Green file: {lastfile.read()}")
            if 'Red' in detector_list:
                lastfile = ktl.cache('kpfred', 'FITSFILE')
                print(f"  Red file:   {lastfile.read()}")

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
#         print(f"    notok: {notok}")
        notok = np.array(notok)

        if np.any(notok):
            print(msg)
            return False
#         print('    Done')
        return True
