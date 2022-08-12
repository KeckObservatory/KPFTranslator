

import ktl
from ddoitranslatormodule.BaseFunction import TranslatorModuleFunction
from ddoitranslatormodule.DDOIExceptions import *

from .. import log, KPFError


class SetExptime(TranslatorModuleFunction):

    def __init__(self):
        super().__init__()

    @classmethod
    def pre_condition(cls, args, logger, cfg):
        print("Pre condition")
        return True

    @classmethod
    def perform(cls, args, logger, cfg):
        exptime = args.get('exptime', None)
        if exptime is not None:
            kpfexpose = ktl.cache('kpfexpose')
            exptime_value = kpfexpose['EXPOSURE'].read()
            if abs(exptime_value - exptime) > 0.1:
                msg = (f"Final exposure time mismatch: "
                       f"{exptime_value:.1f} != {exptime:.1f}")
                log.error(msg)
                raise KPFError(msg)
        log.info('    Done')

    @classmethod
    def post_condition(cls, args, logger, cfg):
        print("Post condition")
        return True
