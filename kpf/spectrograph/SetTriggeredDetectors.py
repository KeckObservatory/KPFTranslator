

import ktl
from ddoitranslatormodule.BaseFunction import TranslatorModuleFunction
from ddoitranslatormodule.DDOIExceptions import *

from ..utils import *


class SetTriggeredDetectors(TranslatorModuleFunction):
    '''Selects which cameras will be triggered by setting the
    `kpfexpose.TRIG_TARG` keyword value.
    '''
    def __init__(self):
        super().__init__()

    @classmethod
    def pre_condition(cls, args, logger, cfg):
        print("Pre condition")
        return True

    @classmethod
    def perform(cls, args, logger, cfg):
        detector_list = []
        if args.get('TriggerRed', False) is True:
            detector_list.append('Red')
        if args.get('TriggerGreen', False) is True:
            detector_list.append('Green')
        if args.get('TriggerCaHK', False) is True:
            detector_list.append('Ca_HK')

        detectors_string = ','.join(detector_list)
        print(f"  Setting triggered detectors to '{detectors_string}'")
        kpfexpose = ktl.cache('kpfexpose')
        kpfexpose['TRIG_TARG'].write(detectors_string)

    @classmethod
    def post_condition(cls, args, logger, cfg):
        kpfexpose = ktl.cache('kpfexpose')
        detectors = kpfexpose['TRIG_TARG'].read()
        detector_list = detectors.split(',')

        red_status = 'Red' in detector_list
        red_target = args.get('TriggerRed', False)
        if red_target != red_status:
            msg = (f"Final Red detector trigger mismatch: "
                   f"{red_status} != {red_target}")
            print(msg)
            return False

        green_status = 'Green' in detector_list
        green_target = args.get('TriggerGreen', False)
        if green_target != green_status:
            msg = (f"Final Green detector trigger mismatch: "
                   f"{green_status} != {green_target}")
            print(msg)
            return False

        CaHK_status = 'Ca_HK' in detector_list
        CaHK_target = args.get('TriggerCaHK', False)
        if CaHK_target != CaHK_status:
            msg = (f"Final Ca HK detector trigger mismatch: "
                   f"{CaHK_status} != {CaHK_target}")
            print(msg)
            return False

        print(f"    Done")
        return True
