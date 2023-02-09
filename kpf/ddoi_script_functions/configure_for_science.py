import ktl

from kpf.KPFTranslatorFunction import KPFTranslatorFunction
from ..scripts.ConfigureForScience import ConfigureForScience
from ..scripts.ConfigureForCalibrations import ConfigureForCalibrations


class configure_for_science(KPFTranslatorFunction):
    '''
    '''
    @classmethod
    def pre_condition(cls, args, logger, cfg):
        return True

    @classmethod
    def perform(cls, args, logger, cfg):
        OBtype = args.get('Template_Name')
        if OBtype == 'kpf_acq':
            ConfigureForScience.execute(args)
        elif OBtype == 'kpf_acq_cal':
            ConfigureForCalibrations.execute(args)
        else:
            raise NotImplementedError(f"Template name {OBtype} not supported")

    @classmethod
    def post_condition(cls, args, logger, cfg):
        return True
