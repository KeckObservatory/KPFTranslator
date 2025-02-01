from pathlib import Path

import ktl

from kpf import log, cfg, check_input
from kpf.exceptions import *
from kpf.KPFTranslatorFunction import KPFFunction, KPFScript
from kpf.guider import guider_is_saving, guider_is_active


class GrabGuiderExposure(KPFFunction):
    '''If the guider is active and saving images, return the filename of the
    next image to be written.

    KTL Keywords Used:

    - `kpfguide.EXPTIME`
    - `kpfguide.LASTFILE`
    - `kpfexpose.OBJECT`
    '''
    @classmethod
    def pre_condition(cls, args):
        if guider_is_active() == False:
            raise FailedPreCondition('Guider is not active')
        if guider_is_saving() == False:
            raise FailedPreCondition('Guider is not saving')

    @classmethod
    def perform(cls, args):
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
    def post_condition(cls, args):
        kpfguide = ktl.cache('kpfguide')
        lastfile = kpfguide['LASTFILE']
        new_file = Path(f"{lastfile.read()}")
        log.debug(f"CRED2 LASTFILE: {new_file}")
        if new_file.exists() == False:
            raise FailedPostCondition(f"Could not find output file: {file}")
