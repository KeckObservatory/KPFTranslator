import numpy as np

import ktl
from ddoitranslatormodule.BaseFunction import TranslatorModuleFunction
from ddoitranslatormodule.DDOIExceptions import *

from ..utils import *


class SetND1(TranslatorModuleFunction):
    '''Set the filter in the ND1 filter wheel (the one at the output of the 
    octagon) via the `kpfmot.ND1POS` keyword.
    '''
    def __init__(self):
        super().__init__()

    @classmethod
    def pre_condition(cls, args, logger, cfg):
        return True

    @classmethod
    def perform(cls, args, logger, cfg):
        ND1_target = args.get('nd1_filter', None)
        if ND1_target is not None:
            print(f"  Setting ND1 to {ND1_target}")
            kpfmot = ktl.cache('kpfmot')
            kpfmot['ND1POS'].write(ND1_target)

    @classmethod
    def post_condition(cls, args, logger, cfg):
        ND1_target = args.get('nd1_filter', None)
        if ND1_target is not None:
            kpfmot = ktl.cache('kpfmot')
            final_pos = kpfmot['ND1POS'].read()
            if final_pos != ND1_target:
                msg = f"Final ND1 position mismatch: {final_pos} != {ND1_target}"
                print(msg)
                return False
            print('    Done')
            return True
