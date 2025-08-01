import ktl

from kpf import log, cfg
from kpf.exceptions import *
from kpf.KPFTranslatorFunction import KPFFunction, KPFScript


class SetCurrentBase(KPFFunction):
    '''Sets the CURRENT_BASE keyword to the value of SCIENCE_BASE or SKY_BASE
    based upon the pointing origin (PO) reported by DCS.  The target pixel for
    tip tilt controll will be this value, but modified by the DAR correction
    and offset guiding parameters.

    KTL Keywords Used:

    - `kpfguide.CURRENT_BASE`
    - `kpfguide.SCIENCE_BASE`
    - `kpfguide.SKY_BASE`
    '''
    @classmethod
    def pre_condition(cls, args):
        pass

    @classmethod
    def perform(cls, args):
        kpfguide = ktl.cache('kpfguide')
        poname = args.get('PO', 'KPF')
        basename = {'KPF': 'SCIENCE_BASE',
                    'SKY': 'SKY_BASE'}[poname]
        log.info(f'Setting CURRENT_BASE to {basename}')
        basexy = kpfguide[basename].read(binary=True)
        log.debug(f"Setting CURRENT_BASE to {basexy}")
        kpfguide['CURRENT_BASE'].write(basexy)

    @classmethod
    def post_condition(cls, args):
        pass