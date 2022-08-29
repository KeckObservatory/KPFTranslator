import numpy as np

import ktl

from .. import KPFTranslatorFunction


class StartExposure(KPFTranslatorFunction):
    '''Begins an triggered exposure by setting the `kpfexpose.EXPOSE` keyword
    to Start.  This will return immediately after.  Use commands like
    WaitForReadout or WaitForReady to determine when an exposure is done.
    '''
    @classmethod
    def pre_condition(cls, args, logger, cfg):
        conditions = []
        kpfexpose = ktl.cache('kpfexpose')
        detectors = kpfexpose['TRIG_TARG'].read()
        detector_list = detectors.split(',')
        if 'Green' in detector_list:
            conditions.append(check_green_detector_power())
            conditions.append(check_green_detector_temperature())
        if 'Red' in detector_list:
            conditions.append(check_red_detector_power())
            conditions.append(check_red_detector_temperature())
        if 'Ca_HK' in detector_list:
            conditions.append(check_cahk_detector_temperature())
        return np.all(conditions)

    @classmethod
    def perform(cls, args, logger, cfg):
        kpfexpose = ktl.cache('kpfexpose')
        expose = kpfexpose['EXPOSE']
        expose.monitor()
        if expose > 0:
            print(f"  Detector(s) are currently {expose} waiting for Ready")
            expose.waitFor('== 0',timeout=300)
        print(f"  Beginning Exposure")
        expose.write('Start')

    @classmethod
    def post_condition(cls, args, logger, cfg):
        kpfexpose = ktl.cache('kpfexpose')
        exptime = kpfexpose['EXPOSURE'].read(binary=True)
        expose = kpfexpose['EXPOSE'].read()
        print(f"    exposure time = {exptime:.1f}")
        print(f"    status = {expose}")
        if exptime > 0.1:
            if expose not in ['Start', 'InProgress', 'End', 'Readout']:
                msg = f"Unexpected EXPOSE status = {expose}"
                print(msg)
                raise KPFError(msg)
        print('    Done')
        return True