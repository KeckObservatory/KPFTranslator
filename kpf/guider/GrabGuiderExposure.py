from pathlib import Path

import ktl

from kpf.KPFTranslatorFunction import KPFTranslatorFunction
from .. import log
from . import guider_is_saving, guider_is_active


class GrabGuiderExposure(KPFTranslatorFunction):
    '''If the guider is active and saving images, return the filename of the
    next image to be written.
    
    ARGS:
    =====
    None
    '''
    @classmethod
    def pre_condition(cls, args, logger, cfg):
        return guider_is_active() and guider_is_saving()

    @classmethod
    def perform(cls, args, logger, cfg):
        kpfguide = ktl.cache('kpfguide')
        kpfexpose = ktl.cache('kpfexpose')
        exptime = kpfguide['EXPTIME'].read(binary=True)
        lastfile = kpfguide['LASTFILE']
        initial_lastfile = lastfile.read()
        log.debug(f"Grabbing next guider exposure.")
        log.debug(f"kpfexpose.OBJECT = {kpfexpose['OBJECT'].read()}")
        expr = f"($kpfguide.LASTFILE != '{initial_lastfile}')"
        success = ktl.waitFor(expr, timeout=exptime*2+1)
        if success is False:
            log.error(f'Failed to get new lastfile from guider')

    @classmethod
    def post_condition(cls, args, logger, cfg):
        kpfguide = ktl.cache('kpfguide')
        lastfile = kpfguide['LASTFILE']
        new_file = Path(f"{lastfile.read()}")
        log.debug(f"CRED2 LASTFILE: {new_file}")
        return new_file.exists()
