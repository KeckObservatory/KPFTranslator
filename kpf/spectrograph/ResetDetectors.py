import time
import ktl

from kpf.KPFTranslatorFunction import KPFTranslatorFunction
from kpf import (log, KPFException, FailedPreCondition, FailedPostCondition,
                 FailedToReachDestination, check_input)


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
        return True

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
        timeout = cfg.get('times', 'kpfexpose_reset_time', fallback=10)
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
