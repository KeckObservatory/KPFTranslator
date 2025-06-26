import ktl

from kpf import log, cfg
from kpf.exceptions import *
from kpf.KPFTranslatorFunction import KPFFunction, KPFScript


class SetAFMtoMirror(KPFFunction):
    '''Set AFM to Mirror so ACAM sees light

    KTL Keywords Used:

    - `ao.OBAMNAME`
    - `ao.OBAMSLEW`
    - `ao.OBAMSTST`
    '''
    @classmethod
    def pre_condition(cls, args):
        pass

    @classmethod
    def perform(cls, args):
        OBAMNAME = ktl.cache('ao', 'OBAMNAME')
        OBAMSLEW = ktl.cache('ao', 'OBAMSLEW')
        log.debug(f"Setting AFM to Mirror")
        OBAMNAME.write('Mirror')
        OBAMSLEW.write('1')

    @classmethod
    def post_condition(cls, args):
        expr = '($ao.OBAMSTST == INPOS) and ($ao.OBAMNAME == Mirror)'
        aoamstst_success = ktl.waitfor(expr, timeout=60)
        if not aoamstst_success:
            OBAMNAME = ktl.cache('ao', 'OBAMNAME')
            FailedToReachDestination(OBAMNAME.read(), 'Mirror')

