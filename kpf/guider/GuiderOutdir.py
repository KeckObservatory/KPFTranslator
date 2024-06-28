from pathlib import Path

import ktl

from kpf.KPFTranslatorFunction import KPFTranslatorFunction
from kpf import (log, KPFException, FailedPreCondition, FailedPostCondition,
                 FailedToReachDestination, check_input)


class GuiderOutdir(KPFTranslatorFunction):
    '''Print the value of the kpfguide.OUTDIR keyword to STDOUT

    KTL Keywords Used:

    - `kpfguide.OUTDIR`
    '''
    @classmethod
    def pre_condition(cls, args, logger, cfg):
        pass

    @classmethod
    def perform(cls, args, logger, cfg):
        kpfguide = ktl.cache('kpfguide')
        outdir = kpfguide['OUTDIR'].read()
        print(outdir)

    @classmethod
    def post_condition(cls, args, logger, cfg):
        pass
