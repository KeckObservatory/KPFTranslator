import time
import ktl

from kpf.KPFTranslatorFunction import KPFTranslatorFunction
from kpf import (log, KPFException, FailedPreCondition, FailedPostCondition,
                 FailedToReachDestination, check_input)


class ResetCaHKDetector(KPFTranslatorFunction):
    '''Resets the Ca HK detector by aborting the exposure

    ARGS: None
    '''
    @classmethod
    def pre_condition(cls, args, logger, cfg):
        pass

    @classmethod
    def perform(cls, args, logger, cfg):
        expose = ktl.cache('kpf_hk', 'EXPOSE')
        log.warning(f"Resetting/Aborting: kpf_hk.EXPOSE = abort")
        expose.write('abort')
        log.debug('Reset/abort command sent')

    @classmethod
    def post_condition(cls, args, logger, cfg):
        expstate = ktl.cache('kpf_hk', 'EXPSTATE')
        timeout = cfg.getfloat('times', 'kpfexpose_reset_time', fallback=10)
        log.warning(f"Waiting for kpf_hk to be Ready")
        success = expstate.waitFor('=="Ready"', timeout=timeout)
        if success is not True:
            raise FailedToReachDestination(expstate.read(), 'Ready')


class ResetGreenDetector(KPFTranslatorFunction):
    '''Resets the kpfgreen detector

    ARGS: None
    '''
    @classmethod
    def pre_condition(cls, args, logger, cfg):
        expstate = ktl.cache('kpfgreen', 'EXPSTATE')
        if expstate.read() == 'Resetting':
            raise FailedPreCondition('Reset already in progress')

    @classmethod
    def perform(cls, args, logger, cfg):
        expose = ktl.cache('kpfgreen', 'EXPOSE')
        log.warning(f"Resetting: kpfgreen.EXPOSE = Reset")
        expose.write('Reset')
        log.debug('Reset command sent')

    @classmethod
    def post_condition(cls, args, logger, cfg):
        expose = ktl.cache('kpfgreen', 'EXPOSE')
        timeout = cfg.getfloat('times', 'kpfexpose_reset_time', fallback=10)
        log.warning(f"Waiting for kpfgreen to be Ready")
        success = expose.waitFor('=="Ready"', timeout=timeout)
        if success is not True:
            raise FailedToReachDestination(expose.read(), 'Ready')


class ResetRedDetector(KPFTranslatorFunction):
    '''Resets the kpfred detector

    ARGS: None
    '''
    @classmethod
    def pre_condition(cls, args, logger, cfg):
        expstate = ktl.cache('kpfred', 'EXPSTATE')
        if expstate.read() == 'Resetting':
            raise FailedPreCondition('Reset already in progress')

    @classmethod
    def perform(cls, args, logger, cfg):
        expose = ktl.cache('kpfred', 'EXPOSE')
        log.warning(f"Resetting: kpfred.EXPOSE = Reset")
        expose.write('Reset')
        log.debug('Reset command sent')

    @classmethod
    def post_condition(cls, args, logger, cfg):
        expose = ktl.cache('kpfred', 'EXPOSE')
        timeout = cfg.getfloat('times', 'kpfexpose_reset_time', fallback=10)
        log.warning(f"Waiting for kpfred to be Ready")
        success = expose.waitFor('=="Ready"', timeout=timeout)
        if success is not True:
            raise FailedToReachDestination(expose.read(), 'Ready')


class ResetDetectors(KPFTranslatorFunction):
    '''Resets the kpfexpose service by setting kpfexpose.EXPOSE = Reset

    Description from Will Deich:
    This sets EXPOSE=Reset for the appropriate service.  For the 
    ktlcamerad services, that just means, “even though you’ve not received
    (from camerad) the normal sequence of messages for a completed exposure,
    pretend everything is fine for starting a new exposure.”
    
    ARGS: None
    '''
    @classmethod
    def pre_condition(cls, args, logger, cfg):
        pass

    @classmethod
    def perform(cls, args, logger, cfg):
        kpfexpose = ktl.cache('kpfexpose')
        log.warning(f"Resetting: kpfexpose.EXPOSE = Reset")
        kpfexpose['EXPOSE'].write('Reset')
        log.debug('Reset command sent')
        time.sleep(1)
        log.debug(f"Current: kpfexpose.EXPOSE = {kpfexpose['EXPOSE'].read()}")

    @classmethod
    def post_condition(cls, args, logger, cfg):
        timeout = cfg.getfloat('times', 'kpfexpose_reset_time', fallback=10)
        log.debug(f'Waiting {timeout:.1f} s for EXPOSE to be Ready')
        expr = f"($kpfexpose.EXPOSE >= Ready)"
        log.warning(f"Waiting for kpfexpose to be Ready")
        success = ktl.waitFor(expr, timeout=timeout)
        if success is not True:
            kpfexposeexpose = ktl.cache('kpfexpose', 'EXPOSE')
            raise FailedToReachDestination(kpfexposeexpose.read(), 'Ready')
        else:
            kpfexpose = ktl.cache('kpfexpose')
            log.info(f"Reset detectors done")
            log.info(f"kpfexpose.EXPOSE = {kpfexpose['EXPOSE'].read()}")
            log.info(f"kpfexpose.EXPLAINR = {kpfexpose['EXPLAINR'].read()}")
