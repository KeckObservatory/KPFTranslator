from pathlib import Path

import ktl

from ddoitranslatormodule.KPFTranslatorFunction import KPFTranslatorFunction
from .. import check_guider_is_saving


class TakeGuiderExposure(KPFTranslatorFunction):
    '''Check for a new file to be written, then returns. The new file can be
    found by looking at the kpfguide.OUTDIR and kpfguide.LASTFILE keywords.
    '''
    @classmethod
    def pre_condition(cls, args, logger, cfg):
        return check_guider_is_saving()

    @classmethod
    def perform(cls, args, logger, cfg):
        kpfguide = ktl.cache('kpfguide')
        exptime = kpfguide['EXPTIME'].read(binary=True)
        outdir = kpfguide['OUTDIR'].read()
        lastfile = kpfguide['LASTFILE']
        lastfile.monitor()
        lastfile.wait(timeout=exptime+1) # Wait for update which signals a new file

    @classmethod
    def post_condition(cls, args, logger, cfg):
        lastfile = kpfguide['LASTFILE']
        lastfile.monitor()
        new_file = Path(outdir) / Path(f"{lastfile}")
        print(f"{new_file}")
        return new_file.exists()
