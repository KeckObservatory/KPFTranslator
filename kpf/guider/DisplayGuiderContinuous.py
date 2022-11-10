import time
from pathlib import Path
import subprocess

import ktl

from ddoitranslatormodule.KPFTranslatorFunction import KPFTranslatorFunction
from .. import (log, KPFException, FailedPreCondition, FailedPostCondition,
                FailedToReachDestination, check_input)
from .GuiderLastfile import GuiderLastfile


class DisplayGuiderContinuous(KPFTranslatorFunction):
    '''Continuously display latest guider images to ds9.
    '''
    @classmethod
    def pre_condition(cls, args, logger, cfg):
        return True

    @classmethod
    def perform(cls, args, logger, cfg):
        display_name = cfg.get('display', 'guider_xpa_target', fallback='CRED2')
        while True:
            GuiderLastfile.execute({'wait': True})
            lastfile = ktl.cache('kpfguide', 'LASTFILE')
            ds9cmd = ['xpaset', display_name, 'fits', f"{lastfile.read()}",
                      '<', f"{lastfile.read()}"]
            log.debug(f"Running: {' '.join(ds9cmd)}")
            subprocess.call(' '.join(ds9cmd), shell=True)
            regfile = Path(f'/home/kpfeng/fibers_on_cred2.reg')
            if regfile.exists() is True:
                overlaycmd = ['xpaset', '-p', display_name, 'regions', 'file',
                              f"{regfile}"]
                log.debug(f"Running: {' '.join(overlaycmd)}")
                subprocess.call(' '.join(overlaycmd), shell=True)

    @classmethod
    def post_condition(cls, args, logger, cfg):
        return True
