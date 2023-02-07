import ktl

from ddoitranslatormodule.KPFTranslatorFunction import KPFTranslatorFunction
from ..scripts.ExecuteSci import ExecuteSci
from ..scripts.ExecuteDark import ExecuteDark
from ..scripts.ExecuteCal import ExecuteCal


class execute_observation(KPFTranslatorFunction):
    '''
    '''
    @classmethod
    def pre_condition(cls, args, logger, cfg):
        return True

    @classmethod
    def perform(cls, args, logger, cfg):
        OBtype = args.get('Template_Name')
        if OBtype == 'kpf_sci':
            ExecuteSci.execute(args)
        elif OBtype == 'kpf_dark':
            ExecuteDark.execute(args)
        elif OBtype == 'kpf_cal':
            ExecuteCal.execute(args)
        else:
            raise NotImplementedError(f"Template name {OBtype} not supported")

    @classmethod
    def post_condition(cls, args, logger, cfg):
        return True
