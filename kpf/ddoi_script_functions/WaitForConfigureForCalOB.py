from time import sleep
from packaging import version

import ktl

from ddoitranslatormodule.KPFTranslatorFunction import KPFTranslatorFunction
from ..calbench import lamp_has_warmed_up
from ..calbench.CalLampPower import CalLampPower


class WaitForConfigureForCalSequence(KPFTranslatorFunction):
    '''
    '''
    @classmethod
    def pre_condition(cls, args, logger, cfg):
        # Check template name
        OB_name = args.get('Template_Name', None)
        if OB_name is None:
            return False
        if OB_name != 'kpf_cal':
            return False
        # Check template version
        OB_version = args.get('Template_Version', None)
        if OB_version is None
            return False
        OB_version = version.parse(OB_version)
        cfg = cls._load_config(cls, cfg)
        compatible_version = version.parse(cfg.get('templates', OB_name))
        if compatible_version != OB_version:
            return False
        return True

    @classmethod
    def perform(cls, args, logger, cfg):
        # Power up needed lamps
        lamps = [x['CalSource'] for x in args.get('SEQ_Calibrations')]
        for lamp in lamps:
            pass
            # add appropriate waitfors here to ensure lamps are warm

    @classmethod
    def post_condition(cls, args, logger, cfg):
        return True

