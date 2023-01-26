from pathlib import Path

import ktl

from KPFTranslatorFunction import KPFTranslatorFunction
from .. import log
from . import guider_is_saving, guider_is_active
from . import TriggerSingleGuiderExposure, GrabGuiderExposure


class TakeGuiderExposure(KPFTranslatorFunction):
    '''Depending on whether the guide camera is running in continuous mode or
    not, this will either grab the next exposure (if in continuous mode) or
    trigger a new exposure.
    
    ARGS: None
    '''
    @classmethod
    def pre_condition(cls, args, logger, cfg):
        return True

    @classmethod
    def perform(cls, args, logger, cfg):
        kpfguide = ktl.cache('kpfguide')
        exptime = kpfguide['EXPTIME'].read(binary=True)
        lastfile = kpfguide['LASTFILE']

        if guider_is_active():
            if guider_is_saving():
                GrabGuiderExposure.GrabGuiderExposure.execute({})
            else:
                # not sure what right action is here
                log.warning('Guider is active, but not saving. No image saved.')
        else:
            TriggerSingleGuiderExposure.TriggerSingleGuiderExposure.execute({})

        lastfile.monitor()
        lastfile.wait(timeout=exptime*2+1) # Wait for update which signals a new file

    @classmethod
    def post_condition(cls, args, logger, cfg):
        return True
