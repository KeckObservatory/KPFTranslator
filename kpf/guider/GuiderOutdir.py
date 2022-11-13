from pathlib import Path

import ktl

from ddoitranslatormodule.KPFTranslatorFunction import KPFTranslatorFunction


class GuiderOutdir(KPFTranslatorFunction):
    '''Print the value of the kpfguide.OUTDIR keyword to STDOUT
    
    ARGS: None
    '''
    @classmethod
    def pre_condition(cls, args, logger, cfg):
        return True

    @classmethod
    def perform(cls, args, logger, cfg):
        kpfguide = ktl.cache('kpfguide')
        outdir = kpfguide['OUTDIR'].read()
        print(outdir)

    @classmethod
    def post_condition(cls, args, logger, cfg):
        return True
