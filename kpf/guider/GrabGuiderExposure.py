from pathlib import Path

import ktl

from ddoitranslatormodule.KPFTranslatorFunction import KPFTranslatorFunction
from .. import log
from . import guider_is_saving, guider_is_active


class GrabGuiderExposure(KPFTranslatorFunction):
    '''If the guider is active and saving images, return the filename of the
    next image to be written.
    '''
    @classmethod
    def pre_condition(cls, args, logger, cfg):
        return guider_is_active() and guider_is_saving()

    @classmethod
    def perform(cls, args, logger, cfg):
        kpfguide = ktl.cache('kpfguide')
        exptime = kpfguide['EXPTIME'].read(binary=True)
        lastfile = kpfguide['LASTFILE']
        lastfile.monitor()
        lastfile.wait(timeout=exptime+1) # Wait for update which signals a new file

    @classmethod
    def post_condition(cls, args, logger, cfg):
        kpfguide = ktl.cache('kpfguide')
        lastfile = kpfguide['LASTFILE']
        lastfile.monitor()
        new_file = Path(f"{lastfile}")
        log.debug(f"CRED2 LASTFILE: {new_file}")
        return new_file.exists()
