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
    
    ARGS:
    =====
    None
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
        exptime = kpfexpose['EXPOSURE'].read(binary=True)
        timeout = 6
        left_start_state = ktl.waitFor(expr, timeout=timeout)
        if left_start_state is False:
            log.error(f'We are still in start state after {timeout} s')
            # Figure out which detector is stuck in the start state?
            green_expstate = ktl.cache('kpfgreen', 'EXPSTATE').read()
            log.debug(f'kpfgreen.EXPSTATE = {green_expstate}')
            red_expstate = ktl.cache('kpfred', 'EXPSTATE').read()
            log.debug(f'kpfred.EXPSTATE = {red_expstate}')
            cahk_expstate = ktl.cache('kpf_hk', 'EXPSTATE').read()
            log.debug(f'kpf_hk.EXPSTATE = {cahk_expstate}')
            # Abort the current exposure
            elapsed = kpfexpose['ELAPSED'].read(binary=True)
            remaining = exptime-elapsed
            if remaining <= 10:
                # Don't stop exposure, just wait it out
                log.debug(f'Waiting out remaining {remaining} s of exposure')
                time.sleep(remaining+2)
            else:
                log.warning('Stopping current exposure (with read out)')
                kpfexpose['EXPOSE'].write('End')
                time.sleep(2) # Time shim, this time is a WAG
            # Now reset the offending detector
            if green_expstate == 'Start':
                ResetGreenDetector.execute({})
            if red_expstate == 'Start':
                ResetRedDetector.execute({})
            if cahk_expstate == 'Start':
                ResetCaHKDetector.execute({})
            # Now start a fresh exposure
            WaitForReady.execute({})
            time.sleep(1.0)          # This time shim and the WaitForReady are hacks to catch if the
            WaitForReady.execute({}) # reset detector went in to readout, but we didn't know.
            log.warning('Restarting exposure')
            StartExposure.execute(args)
