import time

import ktl

from kpf import log, cfg
from kpf.exceptions import *
from kpf.KPFTranslatorFunction import KPFFunction, KPFScript
from kpf.calbench.WaitForLFCReady import WaitForLFCReady


class SetLFCtoAstroComb(KPFFunction):
    '''Set the Laser Frequency Comb (LFC) to "AstroComb" mode. This should
    be used during operation of the LFC.

    KTL Keywords Used:

    - `kpfcal.OPERATIONMODE`
    - `kpfmon.HB_MENLOSTA`

    Functions Called:

    - `kpf.calbench.WaitForLFCReady`
    '''
    @classmethod
    def pre_condition(cls, args):
        heartbeat = ktl.cache('kpfmon', 'HB_MENLOSTA')
        hb_success = heartbeat.waitFor('== "OK"', timeout=3)
        if hb_success is False:
            raise FailedPreCondition(f"Menlo heartbeat is not OK: {heartbeat.read()}")
        lfc_mode = ktl.cache('kpfcal', 'OPERATIONMODE').read()
        if lfc_mode not in ['AstroComb', 'StandbyHigh']:
            raise FailedPreCondition(f"LFC must be in AstroComb or StandbyHigh: {lfc_mode}")

    @classmethod
    def perform(cls, args):
        lfc_mode = ktl.cache('kpfcal', 'OPERATIONMODE')
        log.info('Setting LFC to AstroComb')
        lfc_mode.write('AstroComb')
        time_shim = cfg.getfloat('times', 'LFC_shim_time', fallback=10)
        time.sleep(time_shim)

    @classmethod
    def post_condition(cls, args):
        success = WaitForLFCReady.execute({})
        if success is not True:
            raise FailedPostCondition('LFC did not reach expected state')
