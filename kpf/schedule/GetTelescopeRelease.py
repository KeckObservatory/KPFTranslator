from datetime import datetime, timedelta

from kpf import log, cfg
from kpf.exceptions import *
from kpf.KPFTranslatorFunction import KPFFunction, KPFScript
from kpf.schedule import getTelescopeReadyState


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
        result = getTelescopeReadyState()
        return result.get('State', '') == 'Ready'

    @classmethod
    def post_condition(cls, args):
        pass
