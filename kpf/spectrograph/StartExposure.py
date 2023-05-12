import numpy as np

import ktl

from kpf.KPFTranslatorFunction import KPFTranslatorFunction
from kpf import (log, KPFException, FailedPreCondition, FailedPostCondition,
                 FailedToReachDestination, check_input)
from kpf.spectrograph.WaitForReady import WaitForReady
from kpf.spectrograph.ResetDetectors import ResetGreenDetector, ResetRedDetector


class StartExposure(KPFTranslatorFunction):
    '''Begins an triggered exposure by setting the `kpfexpose.EXPOSE` keyword
    to Start.  This will return immediately after.  Use commands like
    WaitForReadout or WaitForReady to determine when an exposure is done.
    
    ARGS: None
    '''
    @classmethod
    def pre_condition(cls, args, logger, cfg):
        pass

    @classmethod
    def perform(cls, args, logger, cfg):
        expose = ktl.cache('kpfexpose', 'EXPOSE')
        WaitForReady.execute({})
        log.debug(f"Beginning Exposure")
        expose.write('Start')

    @classmethod
    def post_condition(cls, args, logger, cfg):
        expr = f"(kpfexpose.EXPOSE != Start or kpfmon.CAMSTARTSTA != ERROR)"
        timeout = 7 # This is to allow 5s for kpfmon.CAMSTARTSTA to work
        no_timeout = ktl.waitFor(expr, timeout=timeout)
        if no_timeout == True:
            # We didn't time out, so which state is it?
            kpfmon = ktl.cache('kpfmon')
            if kpfmon['CAMSTARTSTA'].read() == 'ERROR':
                log.error('kpfexpose.CAMSTARTSTA is ERROR')
                # Handle start error
                if kpfmon[f"G_STARTSTA"].read() == 'ERROR':
                    log.error('Green STARTSTA is error.')
                    ResetGreenDetector.execute({})
                if kpfmon[f"R_STARTSTA"].read() == 'ERROR':
                    log.error('Red STARTSTA is error.')
                    ResetRedDetector.execute({})
                if kpfmon[f"H_STARTSTA"].read() == 'ERROR':
                    log.error('HK STARTSTA is Error.')
                    log.error('Setting kpfexpose.EXPOSE to End')
                    expose = ktl.cache('kpfexpose', 'EXPOSE')
                    expose.write('End')
                elif kpfmon[f"E_STARTSTA"].read() == 'ERROR':
                    log.error('ExpMeter STARTSTA is Error')
                    log.error('Setting kpfexpose.EXPOSE to End')
                    expose = ktl.cache('kpfexpose', 'EXPOSE')
                    expose.write('End')
            else:
                # We must have transitioned properly
                pass
        else:
            # We timed out, not sure what is going on
            CAMSTARTSTA = ktl.cache('kpfmon', 'CAMSTARTSTA')
            EXPOSE = ktl.cache('kpfexpose', 'EXPOSE')
            msg = f"Neither kpfmon.CAMSTARTSTA nor kpfexpose.EXPOSE transitioned as expected"
            raise KPFException(msg)
