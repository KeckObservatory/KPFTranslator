import ktl

from kpf.KPFTranslatorFunction import KPFTranslatorFunction
from kpf import (log, KPFException, FailedPreCondition, FailedPostCondition,
                 FailedToReachDestination, check_input)


class StartTriggerFile(KPFTranslatorFunction):
    '''Start a "trigger file" from the guide camera.

    KTL Keywords Used:

    - `kpfguide.TRIGCUBE`
    - `kpfguide.TRIGGER`
    '''
    @classmethod
    def pre_condition(cls, args, logger, cfg):
        pass

    @classmethod
    def perform(cls, args, logger, cfg):
        kpfguide = ktl.cache('kpfguide')
        cube = kpfguide['TRIGCUBE'].read()
        log.info(f"Start guider trigger file data collection: TRIGCUBE={cube}")
        kpfguide['TRIGGER'].write('Active')

    @classmethod
    def post_condition(cls, args, logger, cfg):
        pass
