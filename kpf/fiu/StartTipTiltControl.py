import ktl

from ddoitranslatormodule.KPFTranslatorFunction import KPFTranslatorFunction

from . import StartTipTiltCalculations.StartTipTiltCalculations
from .. import (log, KPFException, FailedPreCondition, FailedPostCondition,
                FailedToReachDestination, check_input)


class StartTipTiltControl(KPFTranslatorFunction):
    '''
    '''
    @classmethod
    def pre_condition(cls, args, logger, cfg):
        kpfguide = ktl.cache('kpfguide')
        if kpfguide['CONTINUOUS'].read() is not 'Active':
            raise FailedPreCondition("kpfguide.CONTINUOUS must be Active")
        if kpfguide['TIPTILT'].read() is not 'Active':
            raise FailedPreCondition("kpfguide.TIPTILT must be Active")
        return True

    @classmethod
    def perform(cls, args, logger, cfg):
        StartTipTiltCalculations.execute({})
        tiptilt_control = ktl.cache('kpfguide', 'TIPTILT_CONTROL')
        tiptilt_control.write('Active')

    @classmethod
    def post_condition(cls, args, logger, cfg):
        timeout = cfg.get('times', 'tip_tilt_move_time', fallback=0.1)
        success = ktl.waitFor(f'($kpfguide.TIPTILT_CONTROL == Active)', timeout=timeout)
        if success is not True:
            tiptiltcontrol = ktl.cache('kpfguide', 'TIPTILT_CONTROL')
            raise FailedToReachDestination(tiptiltcontrol.read(), 'Active')
