from kpf import log, cfg
from kpf.exceptions import *
from kpf.KPFTranslatorFunction import KPFFunction, KPFScript


##-------------------------------------------------------------------------
## SendTargetToMagiq
##-------------------------------------------------------------------------
class SendTargetToMagiq(KPFScript):
    '''
    '''
    @classmethod
    def pre_condition(cls, args, OB=None):
        pass

    @classmethod
    def perform(cls, args, OB=None):
        log.info(f'Sending target info to Magiq')
        pass

    @classmethod
    def post_condition(cls, args, OB=None):
        pass
