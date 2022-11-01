

import ktl

from ddoitranslatormodule.KPFTranslatorFunction import KPFTranslatorFunction
from .. import log


class ResetDetectors(KPFTranslatorFunction):
    '''Resets the kpfexpose service by setting kpfexpose.EXPOSE = Reset

    Description from Will Deich:
    This sets EXPOSE=Reset for the appropriate service.  For the 
    ktlcamerad services, that just means, “even though you’ve not received
    (from camerad) the normal sequence of messages for a completed exposure,
    pretend everything is fine for starting a new exposure.”
    '''
    @classmethod
    def pre_condition(cls, args, logger, cfg):
        return True

    @classmethod
    def perform(cls, args, logger, cfg):
        kpfexpose = ktl.cache('kpfexpose')
        log.debug(f"Resetting kpfexpose")
        kpfexpose['EXPOSE'].write('Reset')

    @classmethod
    def post_condition(cls, args, logger, cfg):
        kpfexpose = ktl.cache('kpfexpose')
        timeout = cfg.get('times', 'kpfexpose_reset_time', fallback=10)
        expr = f"($kpfexpose.EXPOSE >= Ready)"
        success = ktl.waitFor(expr, timeout=timeout)
        return success
