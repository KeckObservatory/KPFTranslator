from pathlib import Path

import ktl

from kpf import log, cfg
from kpf.exceptions import *
from kpf.KPFTranslatorFunction import KPFFunction, KPFScript


class GuiderOutdir(KPFFunction):
    '''Print the value of the kpfguide.OUTDIR keyword to STDOUT

    KTL Keywords Used:

    - `kpfguide.OUTDIR`
    '''
    @classmethod
    def pre_condition(cls, args):
        pass

    @classmethod
    def perform(cls, args):
        OUTDIR = ktl.cache('kpfguide', 'OUTDIR')
        OUTDIR.monitor()
        print(OUTDIR.ascii)
        return OUTDIR.ascii

    @classmethod
    def post_condition(cls, args):
        pass
