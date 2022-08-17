import numpy as np

import ktl
from ddoitranslatormodule.BaseFunction import TranslatorModuleFunction
from ddoitranslatormodule.DDOIExceptions import *

from ..utils import *


class SetCalSource(TranslatorModuleFunction):
    '''
    Selects which source is fed from the octagon in to the cal bench via the
    kpfmot.OCTAGON keyword.
    
    Valid names: Home, EtalonFiber, BrdbandFiber, U_gold, U_daily,
    Th_daily, Th_gold, SoCal-CalFib, LFCFiber
    '''
    def __init__(self):
        super().__init__()

    @classmethod
    def pre_condition(cls, args, logger, cfg):
        return True

    @classmethod
    def perform(cls, args, logger, cfg):
        target = args.get('cal_source', 'home')
        kpfmot = ktl.cache('kpfmot')
        print(f"  Setting Cal Source (Octagon) to {target}")
        kpfmot['OCTAGON'].write(target)

    @classmethod
    def post_condition(cls, args, logger, cfg):
        '''Verifies that the final OCTAGON keyword value matches the input.
        '''
        target = args.get('cal_source', 'home')
        kpfmot = ktl.cache('kpfmot')
        final_pos = kpfmot['OCTAGON'].read()
        if final_pos != target:
            msg = f"Final octagon position mismatch: {final_pos} != {target}"
            print(msg)
            return False
        print('    Done')
        return True
