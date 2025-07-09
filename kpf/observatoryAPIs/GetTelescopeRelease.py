import datetime

from kpf import log, cfg
from kpf.exceptions import *
from kpf.KPFTranslatorFunction import KPFFunction, KPFScript
from kpf.observatoryAPIs import query_observatoryAPI


class GetTelescopeRelease(KPFFunction):
    '''

    '''
    @classmethod
    def pre_condition(cls, args):
        pass

    @classmethod
    def perform(cls, args):
        utnow = datetime.datetime.utcnow()
        if utnow.hour > 8:
#             log.debug(f'UT hour > 8 assume release')
            return True
        params = {'telnr': args.get('telnr', 1)}
        result = query_observatoryAPI('schedule', 'getTelescopeReadyState', params)
        log.debug(f'getTelescopeReadyState returned {result}')
        return result.get('State', '') == 'Ready'

    @classmethod
    def post_condition(cls, args):
        pass
