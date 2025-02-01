from pathlib import Path

import ktl

from kpf import log, cfg, check_input
from kpf.exceptions import *
from kpf.KPFTranslatorFunction import KPFFunction, KPFScript
from kpf.guider import guider_is_active, guider_is_saving


class StartGuiderContinuous(KPFFunction):
    '''Put the guider in to continuous exposure mode and set images to be saved.

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
        kpfguide['CONTINUOUS'].write('active')
        kpfguide['SAVE'].write('active')

    @classmethod
    def post_condition(cls, args):
        if guider_is_active() == False:
            raise FailedPostCondition('Guider is not active')
        if guider_is_saving() == False:
            raise FailedPostCondition('Guider is not saving')
