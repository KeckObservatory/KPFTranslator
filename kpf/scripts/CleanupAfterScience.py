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
    :OB: `dict` A fully specified science observing block (OB).
    '''
    @classmethod
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
        log.debug('Clearing target info')
        SetTargetInfo.execute({})
        # Turn off exposure meter controlled exposure
        log.debug('Clearing kpf_expmeter.USETHRESHOLD')
        kpf_expmeter = ktl.cache('kpf_expmeter')
        kpf_expmeter['USETHRESHOLD'].write('No')
        # Set SKY_OFFSET back to 0 0
        log.debug('Clearing kpfguide.SKY_OFFSET')
        sky_offset = ktl.cache('kpfguide', 'SKY_OFFSET')
        sky_offset.write('0 0')

        clear_script_keywords()

    @classmethod
    def post_condition(cls, OB, logger, cfg):
        pass
