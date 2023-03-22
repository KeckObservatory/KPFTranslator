import ktl

from ddoitranslatormodule.KPFTranslatorFunction import KPFTranslatorFunction
from kpf import (log, KPFException, FailedPreCondition, FailedPostCondition,
                 FailedToReachDestination, check_input)


class SetCurrentBase(KPFTranslatorFunction):
    '''Sets the CURRENT_BASE keyword to the value of SCIENCE_BASE or SKY_BASE
    based upon the pointing origin (PO) reported by DCS.  The target pixel for
    tip tilt controll will be this value, but modified by the DAR correction
    and offset guiding parameters.
    
    ARGS:
    =====
    None
    '''
    @classmethod
    def pre_condition(cls, args, logger, cfg):
        return True

    @classmethod
    def perform(cls, args, logger, cfg):
        kpfguide = ktl.cache('kpfguide')
#         poname = ktl.cache('dcs', 'PONAME').read()
        poname = args.get('PO', 'KPF')
        basename = {'KPF': 'SCIENCE_BASE',
                    'SKY': 'SKY_BASE'}[poname]
        log.info(f'Setting CURRENT_BASE to {basename}')
        basexy = kpfguide[basename].read(binary=True)
        log.debug(f"Setting CURRENT_BASE to {basexy}")
        kpfguide['CURRENT_BASE'].write(basexy)

    @classmethod
    def post_condition(cls, args, logger, cfg):
        return True