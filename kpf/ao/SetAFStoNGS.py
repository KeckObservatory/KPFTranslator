import ktl

from kpf import log, cfg
from kpf.exceptions import *
from kpf.KPFTranslatorFunction import KPFFunction, KPFScript


class SetAFStoNGS(KPFFunction):
    '''ACAM should be set to NGS focus. LGS focus will not work for KPF.

    KTL Keywords Used:

    - `ao.OBASNAME`
    - `ao.OBASSLEW`
    - `ao.OBASSTST`
    '''
    @classmethod
    def pre_condition(cls, args):
        pass

    @classmethod
    def perform(cls, args):
        OBASNAME = ktl.cache('ao', 'OBASNAME')
        OBASSLEW = ktl.cache('ao', 'OBASSLEW')
        log.debug(f"Setting AFS to NGS")
        OBASNAME.write('ngs')
        OBASSLEW.write('1')

    @classmethod
    def post_condition(cls, args):
        expr = f'($ao.OBASSTST == INPOS) and ($ao.OBASNAME == ngs)'
        aoamstst_success = ktl.waitfor(expr, timeout=60)
        if not aoamstst_success:
            OBASNAME = ktl.cache('ao', 'OBASNAME')
            raise FailedToReachDestination(OBASNAME.read(), 'ngs')
