from pathlib import Path

import ktl
from ddoitranslatormodule.BaseFunction import TranslatorModuleFunction
from ddoitranslatormodule.DDOIExceptions import *

from . import log, KPFError


class TakeGuiderExposure(TranslatorModuleFunction):

    def __init__(self):
        super().__init__()

    @classmethod
    def pre_condition(cls, args, logger, cfg):
        return check_guider_is_saving()

    @classmethod
    def perform(cls, args, logger, cfg):
        kpfguide = ktl.cache('kpfguide')
        outdir = kpfguide['OUTDIR'].read()
        lastfile = kpfguide['LASTFILE'].read()
        found_new_file = ktl.waitFor(f'($kpfguide.LASTFILE != {lastfile})', timeout=25)
        new_file = Path(outdir) / Path(kpfguide['LASTFILE'].read())

    @classmethod
    def post_condition(cls, args, logger, cfg):
        new_file = Path(outdir) / Path(kpfguide['LASTFILE'].read())
        print(f"New file: {new_file}")
        return new_file.exists()
