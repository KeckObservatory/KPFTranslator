

import ktl
from ddoitranslatormodule.BaseInstrument import InstrumentBase
from ddoitranslatormodule.DDOIExceptions import *

from ..utils import *


class OpenHatch(InstrumentBase):
    '''Open the FIU hatch
    '''
    @classmethod
    def pre_condition(cls, args, logger, cfg):
        return True

    @classmethod
    def perform(cls, args, logger, cfg):
        kpffiu = ktl.cache('kpffiu')
        kpffiu['HATCH'].write('Open')

    @classmethod
    def post_condition(cls, args, logger, cfg):
        return ktl.waitFor('($kpffiu.hatch == Open)', timeout=1)
