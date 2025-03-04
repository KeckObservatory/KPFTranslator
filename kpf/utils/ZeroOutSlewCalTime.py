import time

import ktl

from kpf import log, cfg
from kpf.exceptions import *
from kpf.KPFTranslatorFunction import KPFFunction, KPFScript


##-------------------------------------------------------------------------
## ZeroOutSlewCalTime
##-------------------------------------------------------------------------
class ZeroOutSlewCalTime(KPFFunction):
    '''Zero out the slew cal timer by setting it to the current timestamp.

    ### ARGS
    None
    '''
    @classmethod
    def pre_condition(cls, args):
        pass

    @classmethod
    def perform(cls, args):
        log.debug('Updating LASTSLEWCAL time stamp to reset slew cal timer')
        ktl.write('kpfconfig','LASTSLEWCAL', time.time(), binary=True)

    @classmethod
    def post_condition(cls, args):
        pass
