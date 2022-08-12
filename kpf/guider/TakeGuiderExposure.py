from pathlib import Path

import ktl
from ddoitranslatormodule.BaseFunction import TranslatorModuleFunction
from ddoitranslatormodule.DDOIExceptions import *

from .. import log, KPFError
from ..utils import *

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
        lastfile = kpfguide['LASTFILE']
        lastfile.monitor()
        lastfile.wait(timeout=20)
        new_file = Path(outdir) / Path(f"{lastfile}")

    @classmethod
    def post_condition(cls, args, logger, cfg):
        lastfile = kpfguide['LASTFILE']
        lastfile.monitor()
        new_file = Path(outdir) / Path(f"{lastfile}")
        print(f"New file: {new_file}")
        return new_file.exists()
