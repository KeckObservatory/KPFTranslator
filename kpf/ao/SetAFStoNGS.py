import ktl

from kpf.KPFTranslatorFunction import KPFTranslatorFunction
from kpf import (log, KPFException, FailedPreCondition, FailedPostCondition,
                 FailedToReachDestination, check_input)


class SetAFStoNGS(KPFTranslatorFunction):
    '''# Description
    ACAM should be set to NGS focus. LGS focus will not work for KPF.

    ## KTL Keywords Used
    - `ao.OBASNAME`
    - `ao.OBASSLEW`
    - `ao.OBASSTST`

    ## Scripts Called

    None

    ## Parameters

    None
    '''
    @classmethod
    def pre_condition(cls, args, logger, cfg):
        pass

    @classmethod
    def perform(cls, args, logger, cfg):
        ao = ktl.cache('ao')
        log.debug(f"Setting AFS to NGS")
        ao['OBASNAME'].write('ngs')
        ao['OBASSLEW'].write('1')

    @classmethod
    def post_condition(cls, args, logger, cfg):
        expr = f'($ao.OBASSTST == INPOS) and ($ao.OBASNAME == ngs)'
        aoamstst_success = ktl.waitfor(expr, timeout=60)
        if not aoamstst_success:
            ao = ktl.cache('ao')
            raise FailedToReachDestination(ao['OBASNAME'].read(), 'ngs')
