from pathlib import Path

import ktl

from kpf.KPFTranslatorFunction import KPFTranslatorFunction
from kpf import (log, KPFException, FailedPreCondition, FailedPostCondition,
                 FailedToReachDestination, check_input)
from kpf.scripts import (register_script, obey_scriptrun, check_scriptstop,
                         add_script_log, clear_script_keywords)
from kpf.fiu.StopTipTilt import StopTipTilt
from kpf.spectrograph.StopAgitator import StopAgitator
from kpf.utils.SetTargetInfo import SetTargetInfo


class CleanupAfterScience(KPFTranslatorFunction):
    '''Script which cleans up at the end of Science OBs.

    Can be called by `ddoi_script_functions.post_observation_cleanup`.

    ARGS:
    =====
    None
    '''
    @classmethod
    @obey_scriptrun
    def pre_condition(cls, OB, logger, cfg):
        pass

    @classmethod
    def perform(cls, OB, logger, cfg):
        log.info('-------------------------')
        log.info(f"Running {cls.__name__}")
        log.info('-------------------------')

        StopTipTilt.execute({})

        kpfconfig = ktl.cache('kpfconfig')
        runagitator = kpfconfig['USEAGITATOR'].read(binary=True)
        if runagitator is True:
            StopAgitator.execute({})

        # Clear target info
        SetTargetInfo.execute({})
        # Turn off exposure meter controlled exposure
        kpf_expmeter = ktl.cache('kpf_expmeter')
        kpf_expmeter['USETHRESHOLD'].write('No')

        clear_script_keywords()

    @classmethod
    def post_condition(cls, OB, logger, cfg):
        pass
