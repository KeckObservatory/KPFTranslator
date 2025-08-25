import ktl

from kpf import log, cfg
from kpf.exceptions import *
from kpf.KPFTranslatorFunction import KPFFunction, KPFScript


class IsSoCalClosed(KPFFunction):
    '''Returns True if SoCal enclsoure is closed.

    KTL Keywords Used:

    - `kpfsocal.ENCSTA`
    '''
    @classmethod
    def pre_condition(cls, args):
        pass

    @classmethod
    def perform(cls, args):
        timeout = cfg.getfloat('SoCal', 'enclosure_status_time', fallback=10)
        ENCSTA = ktl.cache('kpfsocal', 'ENCSTA')
        is_closed = ENCSTA.waitFor("==1", timeout=timeout)
        msg = {True: 'SoCal is Closed', False: 'SoCal is NOT Closed'}[is_closed]
        print(msg)
        return is_closed

    @classmethod
    def post_condition(cls, args):
        pass
