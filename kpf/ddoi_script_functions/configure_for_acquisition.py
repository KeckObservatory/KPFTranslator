import ktl

from kpf.KPFTranslatorFunction import KPFTranslatorFunction
from ..scripts.ConfigureForAcquisition import ConfigureForAcquisition


class configure_for_acquisition(KPFTranslatorFunction):
    '''
    '''
    @classmethod
    def pre_condition(cls, args, logger, cfg):
        return True

    @classmethod
    def perform(cls, args, logger, cfg):
        OBtype = args.get('Template_Name')
        if OBtype == 'kpf_acq':
            ConfigureForAcquisition.execute(args)
        else:
            raise NotImplementedError(f"Template name {OBtype} not supported")


    @classmethod
    def post_condition(cls, args, logger, cfg):
        return True
