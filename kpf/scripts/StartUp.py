import time

import ktl

from ddoitranslatormodule.KPFTranslatorFunction import KPFTranslatorFunction
from kpf import (log, KPFException, FailedPreCondition, FailedPostCondition,
                 FailedToReachDestination, check_input)
from kpf.scripts import (register_script, obey_scriptrun, check_scriptstop,
                         add_script_log)
from kpf.utils.SetOutdirs import SetOutdirs
from kpf.spectrograph.WaitForReady import WaitForReady
from kpf.utils.SetObserverFromSchedule import SetObserverFromSchedule
from kpf.utils.StartGUIs import StartGUIs


class StartUp(KPFTranslatorFunction):
    '''Start KPF software for afternoon setup.

    This will set the output directories, set the program ID and observers, and
    bring up the instrument GUIS.

    ARGS:
    =====
    None
    '''
    @classmethod
    @obey_scriptrun
    def pre_condition(cls, args, logger, cfg):
        return True

    @classmethod
    def perform(cls, args, logger, cfg):
        # Set Outdirs
        expose = ktl.cache('kpfexpose', 'EXPOSE')
        if expose.read() != 'Ready':
            log.info('Waiting for kpfexpose to be Ready')
            WaitForReady.execute({})
        SetOutdirs.execute({})
        # Set progname and observer
        SetObserverFromSchedule.execute({})
        # Start GUIs
        StartGUIs.execute({})

    @classmethod
    def post_condition(cls, args, logger, cfg):
        return True
