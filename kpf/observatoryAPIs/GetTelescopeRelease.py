from kpf import log, cfg
from kpf.exceptions import *
from kpf.KPFTranslatorFunction import KPFFunction, KPFScript
from kpf.observatoryAPIs.schedule import query_schedule_API


class GetTelescopeRelease(KPFFunction):
    '''

    '''
    @classmethod
    def pre_condition(cls, args):
        pass

    @classmethod
    def perform(cls, args):
        '''
        '''
        query = 'getTelescopeReadyState'
        params = {'telnr': arge.get('telnr', 1)}
        result = query_schedule_API(query, params)
        log.debug(f'getTelescopeReadyState returned {result}')
        return result.get('State', '') == 'Ready'

    @classmethod
    def post_condition(cls, args):
        pass
