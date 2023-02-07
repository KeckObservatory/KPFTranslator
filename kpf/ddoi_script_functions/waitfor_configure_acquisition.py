import ktl

from ddoitranslatormodule.KPFTranslatorFunction import KPFTranslatorFunction
from ..scripts.WaitForConfigureAcquisition import WaitForConfigureAcquisition


class waitfor_configure_acquisition(KPFTranslatorFunction):
    '''
    '''
    @classmethod
    def pre_condition(cls, args, logger, cfg):
        return True

    @classmethod
    def perform(cls, args, logger, cfg):
        OBtype = args.get('Template_Name')
        if OBtype == 'kpf_acq':
            WaitForConfigureAcquisition.execute(args)
        else:
            raise NotImplementedError(f"Template name {OBtype} not supported")

    @classmethod
    def post_condition(cls, args, logger, cfg):
        return True
