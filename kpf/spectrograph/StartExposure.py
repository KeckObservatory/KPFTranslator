import time

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
        expr = f"(kpfexpose.EXPOSE != Start)"
        kpfexpose = ktl.cache('kpfexpose')
        trig_targ = kpfexpose['TRIG_TARG'].read().split(',')
        if 'Green' in trig_targ:
            expr += ' and ($kpfgreen.EXPSTATE != Start)'
        if 'Red' in trig_targ:
            expr += ' and ($kpfred.EXPSTATE != Start)'
        if 'Ca_HK' in trig_targ:
            expr += ' and ($kpf_hk.EXPSTATE != Start)'
        timeout = 5
        left_start_state = ktl.waitFor(expr, timeout=timeout)
        if left_start_state is False:
            log.error(f'We are still in start state after {timeout} s')
            if 'Green' in trig_targ:
                green_expstate = ktl.cache('kpfgreen', 'EXPSTATE').read()
                log.debug(f'kpfgreen.EXPSTATE = {green_expstate}')
            if 'Red' in trig_targ:
                red_expstate = ktl.cache('kpfred', 'EXPSTATE').read()
                log.debug(f'kpfred.EXPSTATE = {red_expstate}')
            if 'Ca_HK' in trig_targ:
                cahk_expstate = ktl.cache('kpf_hk', 'EXPSTATE').read()
                log.debug(f'kpf_hk.EXPSTATE = {cahk_expstate}')

            # Now we want to abort the current exposure and start again
            log.warning('Stopping current exposure (with read out)')
            kpfexpose['EXPOSE'].write('End')
            time.sleep(2) # Time shim, this time is a WAG

            # This logic is based on the earlier reading of the state, before
            # the exposure was ended
            if 'Green' in trig_targ:
                if green_expstate == 'Start':
                    ResetGreenDetector.execute({})
            if 'Red' in trig_targ:
                if red_expstate == 'Start':
                    ResetRedDetector.execute({})
            if 'Ca_HK' in trig_targ:
                if cahk_expstate == 'Start':
                    ResetCaHKDetector.execute({})

            WaitForReady.execute({})
            StartExposure.execute(args)

#     @classmethod
#     def post_condition(cls, args, logger, cfg):
#         expr = f"(kpfexpose.EXPOSE != Start or kpfmon.CAMSTATESTA == ERROR)"
#         timeout = 7 # This is to allow 5s for kpfmon.CAMSTATESTA to work
#         error_or_exposure_inprogress = ktl.waitFor(expr, timeout=timeout)
#         if error_or_exposure_inprogress == True:
#             # We didn't time out, so which state is it?
#             kpfmon = ktl.cache('kpfmon')
#             camstatesta = kpfmon['CAMSTATESTA'].read()
#             if camstatesta == 'ERROR':
#                 log.error('kpfexpose.CAMSTATESTA is ERROR')
#                 RecoverDetectors.execute({})
#                 # Now we want to abort the current exposure and start again
#                 log.warning('Stopping current exposure (with read out)')
#                 expose = ktl.cache('kpfexpose', 'EXPOSE')
#                 expose.write('End')
#                 WaitForReady.execute({})
#                 StartExposure.execute(args)
#             else:
#                 # We must have transitioned properly
#                 expose = ktl.cache('kpfexpose', 'EXPOSE')
#                 log.debug(f'Post condition succeeded: kpfmon.CAMSTATESTA={camstatesta}, kpfexpose.EXPOSE={expose.read()}')
#         else:
#             # We timed out, not sure what is going on
#             msg = f"Neither kpfmon.CAMSTATESTA nor kpfexpose.EXPOSE transitioned as expected"
#             raise KPFException(msg)
