import ktl

from kpf import log, cfg, check_input
from kpf.exceptions import *
from kpf.KPFTranslatorFunction import KPFFunction, KPFScript


class IsSoCalOpen(KPFFunction):
    '''Returns True if SoCal enclsoure is open.

    ARGS:
    =====
    None
    '''
    @classmethod
    def pre_condition(cls, args):
        pass

    @classmethod
    def perform(cls, args):
        timeout = cfg.getfloat('SoCal', 'enclosure_status_time', fallback=10)
        ENCSTA = ktl.cache('kpfsocal', 'ENCSTA')
        is_open = ENCSTA.waitFor("==0", timeout=timeout)
        msg = {True: 'SoCal is Open', False: 'SoCal is NOT Open'}[is_open]
        print(msg)
        return is_open

    @classmethod
    def post_condition(cls, args):
        pass
