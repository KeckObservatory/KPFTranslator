from pathlib import Path

import ktl

from kpf import log, cfg
from kpf.exceptions import *
from kpf.KPFTranslatorFunction import KPFFunction, KPFScript
from kpf.fiu.StopTipTilt import StopTipTilt
from kpf.spectrograph.StopAgitator import StopAgitator
from kpf.scripts.SetTargetInfo import SetTargetInfo


class CleanupAfterScience(KPFScript):
    '''Script which cleans up at the end of Science OBs.

    Args:
        OB (ObservingBlock): A valid observing block (OB).

    KTL Keywords Used:

    - `kpfconfig.USEAGITATOR`
    - `kpf_expmeter.USETHRESHOLD`
    - `kpfguide.SKY_OFFSET`

    Functions Called:

    - `kpf.fiu.StopTipTilt`
    - `kpf.spectrograph.StopAgitator`
    - `kpf.scripts.SetTargetInfo`
    '''
    @classmethod
    def pre_condition(cls, args, OB=None):
        pass

    @classmethod
    def perform(cls, args, OB=None):
        if isinstance(OB, dict):
            OB = ObservingBlock(OB)
        log.info('-------------------------')
        log.info(f"Running {cls.__name__}")
        log.info('-------------------------')

        StopTipTilt.execute({})

        SCRIPTMSG = ktl.cache('kpfconfig', 'SCRIPTMSG')
        SCRIPTMSG.write('')

        runagitator = ktl.cache('kpfconfig', 'USEAGITATOR').read(binary=True)
        if runagitator is True:
            StopAgitator.execute({})

        # Turn off exposure meter controlled exposure
        log.debug('Clearing kpf_expmeter.USETHRESHOLD')
        USETHRESHOLD = ktl.cache('kpf_expmeter', 'USETHRESHOLD')
        USETHRESHOLD.write('No')
        # Set SKY_OFFSET back to 0 0
        log.debug('Clearing kpfguide.SKY_OFFSET')
        sky_offset = ktl.cache('kpfguide', 'SKY_OFFSET')
        sky_offset.write('0 0')

    @classmethod
    def post_condition(cls, args, OB=None):
        pass
