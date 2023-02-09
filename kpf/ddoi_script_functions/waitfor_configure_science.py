import ktl

from kpf.KPFTranslatorFunction import KPFTranslatorFunction
from ..scripts.WaitForConfigureScience import WaitForConfigureScience


class waitfor_configure_science(KPFTranslatorFunction):
    '''
    '''
    @classmethod
    def pre_condition(cls, args, logger, cfg):
        return True

    @classmethod
    def perform(cls, args, logger, cfg):
        OBtype = args.get('Template_Name')
        if OBtype == 'kpf_acq':
            WaitForConfigureScience.execute(args)
        elif OBtype == 'kpf_acq_cal':
            WaitForConfigureCalibrations.execute(args)
        else:
            raise NotImplementedError(f"Template name {OBtype} not supported")

    @classmethod
    def post_condition(cls, args, logger, cfg):
        return True
