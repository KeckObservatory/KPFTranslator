from pathlib import Path

import ktl
from ddoitranslatormodule.BaseInstrument import InstrumentBase
from ddoitranslatormodule.DDOIExceptions import *

from ..utils import *

class TakeGuiderExposure(InstrumentBase):
    '''Check for a new file to be written, then returns. The new file can be
    found by looking at the kpfguide.OUTDIR and kpfguide.LASTFILE keywords.
    '''
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
        lastfile.wait(timeout=20) # Wait for update which signals a new file

    @classmethod
    def post_condition(cls, args, logger, cfg):
        lastfile = kpfguide['LASTFILE']
        lastfile.monitor()
        new_file = Path(outdir) / Path(f"{lastfile}")
        print(f"New file: {new_file}")
        return new_file.exists()
