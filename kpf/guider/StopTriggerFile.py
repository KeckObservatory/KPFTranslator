import time
from pathlib import Path

import ktl

from kpf import log, cfg
from kpf.exceptions import *
from kpf.KPFTranslatorFunction import KPFFunction, KPFScript


class StopTriggerFile(KPFFunction):
    '''Stop a "trigger file" from the guide camera.

    KTL Keywords Used:

    - `kpfguide.TRIGGER`
    '''
    @classmethod
    def pre_condition(cls, args):
        pass

    @classmethod
    def perform(cls, args):
        TRIGGER = ktl.cache('kpfguide', 'TRIGGER')
        log.info(f"Stopping guider trigger file data collection")
        TRIGGER.write('Inactive')

    @classmethod
    def post_condition(cls, args):
        pass
