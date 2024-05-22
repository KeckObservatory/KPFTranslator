import time

import ktl

from kpf.KPFTranslatorFunction import KPFTranslatorFunction
from kpf import (log, KPFException, FailedPreCondition, FailedPostCondition,
                 FailedToReachDestination, check_input)
from kpf.scripts import (register_script, obey_scriptrun, check_scriptstop,
                         add_script_log)
from kpf.utils.StartGUIs import StartGUIs


class StartUp(KPFTranslatorFunction):
    '''Start KPF software for afternoon setup.

    ARGS:
    =====
    None
    '''
    @classmethod
    def pre_condition(cls, args, logger, cfg):
        pass

    @classmethod
    def perform(cls, args, logger, cfg):
        # Start GUIs
        StartGUIs.execute({})

    @classmethod
    def post_condition(cls, args, logger, cfg):
        pass
