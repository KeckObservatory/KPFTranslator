import time

import ktl

from kpf import log, cfg
from kpf.exceptions import *
from kpf.KPFTranslatorFunction import KPFFunction, KPFScript


class WaitForLFCReady(KPFFunction):
    '''Wait for the Laser Frequency Comb (LFC) to be ready and in "AstroComb"
    mode

    KTL Keywords Used:

    - `kpfmon.HB_MENLOSTA`
    - `kpfmon.LFCREADYSTA`
    - `kpfcal.WOBBLE`
    - `kpfcal.OPERATIONMODE`
    - `kpfcal.SPECFLAT`
    '''
    @classmethod
    def pre_condition(cls, args):
        pass

    @classmethod
    def perform(cls, args):
        expr = f"($kpfmon.HB_MENLOSTA == 'OK')"
        expr += f"and ($kpfmon.LFCREADYSTA == 'OK')"
        expr += f"and ($kpfcal.WOBBLE == 'False')"
        expr += f"and ($kpfcal.OPERATIONMODE == 'AstroComb')"
        expr += f"and ($kpfcal.SPECFLATIR == 'True')"
        expr += f"and ($kpfcal.SPECFLATVIS == 'True')"
        timeout = cfg.getfloat('times', 'LFC_startup_time', fallback=300)
        success = ktl.waitFor(expr, timeout=timeout)
        return success

    @classmethod
    def post_condition(cls, args):
        pass
