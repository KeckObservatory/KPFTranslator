import time
import subprocess

import ktl

from kpf.KPFTranslatorFunction import KPFTranslatorFunction
from kpf import (log, KPFException, FailedPreCondition, FailedPostCondition,
                 FailedToReachDestination, check_input, LostTipTiltStar)


class PowerCycleCaHK(KPFTranslatorFunction):
    '''Script which will power cycle the Ca HK detector control system and
    restart the services. Use as a last resort measure after other
    troubleshooting measures such as resetting the detector and restarting
    software have already failed.
    
    ARGS:
    =====
    None
    '''
    @classmethod
    def pre_condition(cls, args, logger, cfg):
        kpfpower = ktl.cache('kpfpower')
        outlets = [('J1', 'kpfexpose2 Galil RIO controller'),
                   ('J2', 'kpfexpose2 Galil output bank'),
                   ('J5', 'Andor Newton PS'),
                   ]
        for outlet_id, outlet_name in outlets:
            name = kpfpower[f'OUTLET_{outlet_id}_NAME'].read()
            if name.find(outlet_name) < 0:
                raise FailedPreCondition(f"Outlet name: {outlet_id} != '{outlet_name}'")

    @classmethod
    def perform(cls, args, logger, cfg):
        log.warning('Power cycling the Ca HK detector system')
        kpfpower = ktl.cache('kpfpower')
        outlets = [('J1', 'kpfexpose2 Galil RIO controller'),
                   ('J2', 'kpfexpose2 Galil output bank'),
                   ('J5', 'Andor Newton PS'),
                   ]
        for outlet_id, outlet_name in outlets:
            log.debug(f"Powering off {outlet_id}: {outlet_name}")
            kpfpower[f'OUTLET_{outlet_id}'].write('Off')
        time.sleep(10)
        for outlet_id, outlet_name in outlets:
            log.debug(f"Powering on {outlet_id}: {outlet_name}")
            kpfpower[f'OUTLET_{outlet_id}'].write('On')
        time.sleep(10)

        log.warning('Resarting kpf_hk keyword service')
        cmd = ['kpf', 'restart', 'kpf_hk']
        result = subprocess.run(cmd, stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE)
        log.debug(f"  args: {result.args}")
        log.debug(f"  rtncode: {result.returncode}")
        log.debug(f"  STDOUT: {result.stdout.decode()}")
        log.debug(f"  STDERR: {result.stderr.decode()}")
        if result.returncode != 0:
            raise FailedPostCondition(f"The kpf restart kpf_hk command appears to have failed")

    @classmethod
    def post_condition(cls, args, logger, cfg):
        pass
