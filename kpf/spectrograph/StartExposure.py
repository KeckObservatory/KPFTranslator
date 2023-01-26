import numpy as np

import ktl

from kpf.KPFTranslatorFunction import KPFTranslatorFunction
from .. import (log, KPFException, FailedPreCondition, FailedPostCondition,
                FailedToReachDestination, check_input)
from . import (green_detector_power_is_on, green_detector_temperature_is_ok,
               red_detector_power_is_on, red_detector_temperature_is_ok,
               cahk_detector_temperature_is_ok)
from .WaitForReady import WaitForReady


class StartExposure(KPFTranslatorFunction):
    '''Begins an triggered exposure by setting the `kpfexpose.EXPOSE` keyword
    to Start.  This will return immediately after.  Use commands like
    WaitForReadout or WaitForReady to determine when an exposure is done.
    
    ARGS: None
    '''
    @classmethod
    def pre_condition(cls, args, logger, cfg):
        kpfexpose = ktl.cache('kpfexpose')
        detectors = kpfexpose['TRIG_TARG'].read()
        detector_list = detectors.split(',')
        if 'Green' in detector_list:
            green_detector_power_is_on()
            tol = cfg.get('tolerances', 'green_detector_temperature_tolerance',
                          fallback=10)
            green_detector_temperature_is_ok(temperature_tolerance=tol)
        if 'Red' in detector_list:
            red_detector_power_is_on()
            tol = cfg.get('tolerances', 'red_detector_temperature_tolerance',
                          fallback=10)
            red_detector_temperature_is_ok(temperature_tolerance=tol)
        if 'Ca_HK' in detector_list:
            tol = cfg.get('tolerances', 'cahk_detector_temperature_tolerance',
                          fallback=10)
            cahk_detector_temperature_is_ok(temperature_tolerance=tol)
        return True

    @classmethod
    def perform(cls, args, logger, cfg):
        kpfexpose = ktl.cache('kpfexpose')
        expose = kpfexpose['EXPOSE']
        WaitForReady.execute({})
        log.debug(f"Beginning Exposure")
        expose.write('Start')

    @classmethod
    def post_condition(cls, args, logger, cfg):
        kpfexpose = ktl.cache('kpfexpose')
        exptime = kpfexpose['EXPOSURE'].read(binary=True)
        shim_time = cfg.get('times', 'kpfexpose_response_time', fallback=1)
        success = ktl.waitFor(f"(kpfexpose.EXPOSE != InProgress)", timeout=shim_time)
        if success is not True:
            raise FailedToReachDestination(kpfexpose['EXPOSE'].read(),
                                     ['Start', 'InProgress', 'End', 'Readout'])
