import ktl

from ddoitranslatormodule.KPFTranslatorFunction import KPFTranslatorFunction
from .. import (log, KPFException, FailedPreCondition, FailedPostCondition,
                FailedToReachDestination, check_input)


class UpdateCurrentBase(KPFTranslatorFunction):
    '''
    
    ARGS: None
    '''
    @classmethod
    def pre_condition(cls, args, logger, cfg):
        return True

    @classmethod
    def perform(cls, args, logger, cfg):
        kpfguide = ktl.cache('kpfguide')
        poname = ktl.cache('dcs', 'PONAME').read()
        basename = {'KPF': 'SCIENCE_BASE',
                    'SKY': 'SKY_BASE'}[poname]
        log.info(f'Setting CURRENT_BASE to {basename}')
        basexy = kpfguide[basename].read(binary=True)
        log.debug(f"Setting CURRENT_BASE to {basexy}")
        kpfguide['CURRENT_BASE'].write(basexy)

    @classmethod
    def post_condition(cls, args, logger, cfg):
        return True