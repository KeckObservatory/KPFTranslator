import numpy as np

import ktl

from .. import KPFTranslatorFunction


class SetND2(KPFTranslatorFunction):
    '''Set the filter in the ND2 filter wheel (the one at the output of the 
    octagon) via the `kpfmot.ND2POS` keyword.
    '''
    @classmethod
    def pre_condition(cls, args, logger, cfg):
        return True

    @classmethod
    def perform(cls, args, logger, cfg):
        ND2_target = args.get('nd2_filter', None)
        if ND2_target is not None:
            print(f"  Setting ND2 to {ND2_target}")
            kpfmot = ktl.cache('kpfmot')
            kpfmot['ND2POS'].write(ND2_target)

    @classmethod
    def post_condition(cls, args, logger, cfg):
        ND2_target = args.get('nd2_filter', None)
        if ND2_target is not None:
            kpfmot = ktl.cache('kpfmot')
            final_pos = kpfmot['ND2POS'].read()
            if final_pos != ND2_target:
                msg = f"Final ND2 position mismatch: {final_pos} != {ND2_target}"
                print(msg)
                return False
            print('    Done')
            return True
