from pathlib import Path

import ktl

from ddoitranslatormodule.KPFTranslatorFunction import KPFTranslatorFunction
from .. import log
from . import guider_is_saving, guider_is_active


class TriggerSingleGuiderExposure(KPFTranslatorFunction):
    '''Trigger a single guider exposure using the EXPOSE keyword.
    '''
    @classmethod
    def pre_condition(cls, args, logger, cfg):
        return not guider_is_active() and not guider_is_saving()

    @classmethod
    def perform(cls, args, logger, cfg):
        kpfguide = ktl.cache('kpfguide')
        exptime = kpfguide['EXPTIME'].read(binary=True)
        kpfguide['EXPOSE'].write('yes')
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
