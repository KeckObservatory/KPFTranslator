from pathlib import Path

import ktl

from kpf import log, cfg, check_input
from kpf.exceptions import *
from kpf.KPFTranslatorFunction import KPFFunction, KPFScript
from kpf.guider import guider_is_saving, guider_is_active
from kpf.guider.TriggerSingleGuiderExposure import TriggerSingleGuiderExposure
from kpf.guider.GrabGuiderExposure import GrabGuiderExposure


class TakeGuiderExposure(KPFFunction):
    '''Depending on whether the guide camera is running in continuous mode or
    not, this will either grab the next exposure (if in continuous mode) or
    trigger a new exposure.

    KTL Keywords Used:

    - `kpfguide.EXPTIME`
    - `kpfguide.LASTFILE`

    Scripts Called:

    - `kpf.guider.TriggerSingleGuiderExposure`
    - `kpf.guider.GrabGuiderExposure`
    '''
    @classmethod
    def pre_condition(cls, args):
        pass

    @classmethod
    def perform(cls, args):
        kpfguide = ktl.cache('kpfguide')
        exptime = kpfguide['EXPTIME'].read(binary=True)
        lastfile = kpfguide['LASTFILE']

        if guider_is_active():
            if guider_is_saving():
                GrabGuiderExposure.execute({})
            else:
                # not sure what right action is here
                log.warning('Guider is active, but not saving. No image saved.')
        else:
            TriggerSingleGuiderExposure.execute({})

        lastfile.monitor()
        lastfile.wait(timeout=exptime*2+1) # Wait for update which signals a new file

    @classmethod
    def post_condition(cls, args):
        pass
