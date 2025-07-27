import time
import ktl

from kpf import log, cfg
from kpf.exceptions import *
from kpf.KPFTranslatorFunction import KPFFunction, KPFScript
from kpf.spectrograph.QueryReadMode import QueryReadMode


class QueryFastReadMode(KPFFunction):
    '''Returns True if both ACF files are consistent with fast read mode.

    ARGS:
    =====
    None
    '''
    @classmethod
    def pre_condition(cls, args):
        pass

    @classmethod
    def perform(cls, args):
        green_mode, red_mode = QueryReadMode.execute({})
        return (green_mode == 'fast') and (red_mode == 'fast')

    @classmethod
    def post_condition(cls, args):
        pass
