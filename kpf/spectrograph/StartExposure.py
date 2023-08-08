import numpy as np

import ktl

from kpf.KPFTranslatorFunction import KPFTranslatorFunction
from kpf import (log, KPFException, FailedPreCondition, FailedPostCondition,
                 FailedToReachDestination, check_input)
from kpf.spectrograph.WaitForReady import WaitForReady
from kpf.spectrograph.ResetDetectors import *


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
        expr = f"(kpfexpose.EXPOSE != Start or kpfmon.CAMSTATESTA == ERROR)"
        timeout = 7 # This is to allow 5s for kpfmon.CAMSTATESTA to work
        error_or_exposure_inprogress = ktl.waitFor(expr, timeout=timeout)
        if error_or_exposure_inprogress == True:
            # We didn't time out, so which state is it?
            kpfmon = ktl.cache('kpfmon')
            if kpfmon['CAMSTATESTA'].read() == 'ERROR':
                log.error('kpfexpose.CAMSTATESTA is ERROR')
                RecoverDetectors.execute({})
                # Now we want to abort the current exposure and start again
                log.warning('Stopping current exposure (with read out)')
                expose = ktl.cache('kpfexpose', 'EXPOSE')
                expose.write('End')
                WaitForReady.execute({})
                StartExposure.execute(args)
            else:
                # We must have transitioned properly
                pass
        else:
            # We timed out, not sure what is going on
            msg = f"Neither kpfmon.CAMSTATESTA nor kpfexpose.EXPOSE transitioned as expected"
            raise KPFException(msg)
