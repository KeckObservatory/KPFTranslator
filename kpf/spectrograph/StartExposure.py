import numpy as np

import ktl

from ddoitranslatormodule.KPFTranslatorFunction import KPFTranslatorFunction
from .. import log
from . import (green_detector_power_is_on, green_detector_temperature_is_ok,
               red_detector_power_is_on, red_detector_temperature_is_ok,
               cahk_detector_temperature_is_ok)


class StartExposure(KPFTranslatorFunction):
    '''Begins an triggered exposure by setting the `kpfexpose.EXPOSE` keyword
    to Start.  This will return immediately after.  Use commands like
    WaitForReadout or WaitForReady to determine when an exposure is done.
    
    ARGS: None
    '''
    @classmethod
    def pre_condition(cls, args, logger, cfg):
        conditions = []
        kpfexpose = ktl.cache('kpfexpose')
        detectors = kpfexpose['TRIG_TARG'].read()
        detector_list = detectors.split(',')
        if 'Green' in detector_list:
            conditions.append(green_detector_power_is_on())
            conditions.append(green_detector_temperature_is_ok())
        if 'Red' in detector_list:
            conditions.append(green_detector_power_is_on())
            conditions.append(red_detector_temperature_is_ok())
        if 'Ca_HK' in detector_list:
            conditions.append(cahk_detector_temperature_is_ok())
        return np.all(conditions)

    @classmethod
    def perform(cls, args, logger, cfg):
        kpfexpose = ktl.cache('kpfexpose')
        expose = kpfexpose['EXPOSE']
        expose.monitor()
        if expose > 0:
            log.debug(f"Detector(s) are currently {expose} waiting for Ready")
            expose.waitFor('== 0',timeout=300)
        log.debug(f"Beginning Exposure")
        expose.write('Start')

    @classmethod
    def post_condition(cls, args, logger, cfg):
        kpfexpose = ktl.cache('kpfexpose')
        exptime = kpfexpose['EXPOSURE'].read(binary=True)
        expose = kpfexpose['EXPOSE'].read()
        log.debug(f"    exposure time = {exptime:.1f}")
        log.debug(f"    status = {expose}")
        if exptime > 0.1:
            if expose not in ['Start', 'InProgress', 'End', 'Readout']:
                msg = f"Unexpected EXPOSE status = {expose}"
                log.error(msg)
        return True
