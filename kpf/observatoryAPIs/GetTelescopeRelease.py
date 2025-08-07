import datetime

from kpf import log, cfg
from kpf.exceptions import *
from kpf.KPFTranslatorFunction import KPFFunction, KPFScript
from kpf.observatoryAPIs import query_observatoryAPI


class GetTelescopeRelease(KPFFunction):
    '''Return a boolean indicating whether the telescope has been released.

    Note that this uses the schedule API which resets at local midnight, so if
    the current time is after midnight and before 8am, this assumes release.
    '''
    @classmethod
    def pre_condition(cls, args):
        pass

    @classmethod
    def perform(cls, args):
        utnow = datetime.datetime.utcnow()
        if utnow.hour >= 10 and utnow.hour < 18:
#             log.debug(f'UT hour > 10 assume release')
            return True
        params = {'telnr': args.get('telnr', 1)}
        result = query_observatoryAPI('schedule', 'getTelescopeReadyState', params)
        log.debug(f'getTelescopeReadyState returned {result}')
        return result.get('State', '') == 'Ready'

    @classmethod
    def post_condition(cls, args):
        pass
