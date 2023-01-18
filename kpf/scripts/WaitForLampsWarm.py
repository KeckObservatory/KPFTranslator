from time import sleep
from packaging import version
from pathlib import Path

import ktl

from ddoitranslatormodule.KPFTranslatorFunction import KPFTranslatorFunction
from .. import (log, KPFException, FailedPreCondition, FailedPostCondition,
                FailedToReachDestination, check_input)
from ..calbench.WaitForLampWarm import WaitForLampWarm


class WaitForLampsWarm(KPFTranslatorFunction):
    '''Script which waits all the lamps to be warmed up.
    '''
    @classmethod
    def pre_condition(cls, OB, logger, cfg):
        check_input(OB, 'Template_Name', allowed_values=['kpf_cal'])
        check_input(OB, 'Template_Version', version_check=True, value_min='0.3')
        return True

    @classmethod
    def perform(cls, OB, logger, cfg):
        sequence = OB.get('SEQ_Calibrations', [])
        lamps = set([x['CalSource'] for x in sequence if x['CalSource'] != 'Home'])
        for lamp in lamps:
            log.info(f"Waiting for {lamp} lamp to be warm")
            WaitForLampWarm.execute({'lamp': lamp})

    @classmethod
    def post_condition(cls, args, logger, cfg):
        return True
