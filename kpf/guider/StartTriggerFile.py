import ktl

from kpf import log, cfg
from kpf.exceptions import *
from kpf.KPFTranslatorFunction import KPFFunction, KPFScript


class StartTriggerFile(KPFFunction):
    '''Start a "trigger file" from the guide camera.

    KTL Keywords Used:

    - `kpfguide.TRIGCUBE`
    - `kpfguide.TRIGGER`
    '''
    @classmethod
    def pre_condition(cls, args):
        pass

    @classmethod
    def perform(cls, args):
        kpfguide = ktl.cache('kpfguide')
        cube = kpfguide['TRIGCUBE'].read()
        log.info(f"Start guider trigger file data collection: TRIGCUBE={cube}")
        kpfguide['TRIGGER'].write('Active')

    @classmethod
    def post_condition(cls, args):
        pass
