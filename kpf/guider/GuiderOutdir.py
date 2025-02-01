from pathlib import Path

import ktl

from kpf import log, cfg, check_input
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
        kpfguide = ktl.cache('kpfguide')
        outdir = kpfguide['OUTDIR'].read()
        print(outdir)

    @classmethod
    def post_condition(cls, args):
        pass
