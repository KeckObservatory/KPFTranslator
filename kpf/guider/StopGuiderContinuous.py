from pathlib import Path

import ktl

from kpf import log, cfg
from kpf.exceptions import *
from kpf.KPFTranslatorFunction import KPFFunction, KPFScript
from kpf.guider import guider_is_active, guider_is_saving


class StopGuiderContinuous(KPFFunction):
    '''Stop the guider's continuous exposure mode and stop saving images.

    KTL Keywords Used:

    - `kpfguide.CONTINUOUS`
    - `kpfguide.SAVE`
    '''
    @classmethod
    def pre_condition(cls, args):
        pass

    @classmethod
    def perform(cls, args):
        kpfguide = ktl.cache('kpfguide')
        kpfguide['CONTINUOUS'].write('inactive')
        kpfguide['SAVE'].write('inactive')

    @classmethod
    def post_condition(cls, args):
        if guider_is_active() != False:
            raise FailedPostCondition('Guider is not inactive')
        if guider_is_saving() != False:
            raise FailedPostCondition('Guider is still saving')
