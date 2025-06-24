from kpf import log, cfg
from kpf.exceptions import *
from kpf.KPFTranslatorFunction import KPFFunction, KPFScript
from kpf.magiq.SelectTarget import SelectTarget


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
        pass
#         log.info(f'Sending target info to Magiq')
#         SelectTarget.execute(OB.Target.to_dict())

    @classmethod
    def post_condition(cls, args, OB=None):
        pass
