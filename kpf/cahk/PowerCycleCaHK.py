import time
import subprocess

import ktl

from kpf import log, cfg, check_input
from kpf.exceptions import *
from kpf.KPFTranslatorFunction import KPFFunction, KPFScript
from kpf.spectrograph.ResetDetectors import ResetCaHKDetector


class PowerCycleCaHK(KPFFunction):
    '''Script which will power cycle the Ca HK detector control system and
    restart the services. Use as a last resort measure after other
    troubleshooting measures such as resetting the detector and restarting
    software have already failed.

    KTL Keywords Used:

    - `kpfpower.OUTLET_J1%`
    - `kpfpower.OUTLET_J2%`
    - `kpfpower.OUTLET_J5%`

    Scripts Called:

    -`kpf start/stop/status/restart kpfexpose2`
    -`kpf start/stop/status/restart kpf_hk`
    '''
    @classmethod
    def pre_condition(cls, args):
        kpfpower = ktl.cache('kpfpower')
        outlets = [('J1', 'Galil RIO (expose2)'),
                   ('J2', 'Galil Output Bank (expose2)'),
                   ('J5', 'Andor Newton (kpf_hk)'),
                   ]
        for outlet_id, outlet_name in outlets:
            name = kpfpower[f'OUTLET_{outlet_id}_NAME'].read()
            if name.find(outlet_name) < 0:
                raise FailedPreCondition(f"Outlet name: {outlet_id} != '{outlet_name}'")

    @classmethod
    def perform(cls, args):
        log.warning('Stopping kpfexpose2 dispatcher')
        cmd = ['kpf', 'stop', 'kpfexpose2']
        result = subprocess.run(cmd, stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE)
        log.debug(f"  args: {result.args}")
        log.debug(f"  rtncode: {result.returncode}")
        log.debug(f"  STDOUT: {result.stdout.decode()}")
        log.debug(f"  STDERR: {result.stderr.decode()}")
        if result.returncode != 0:
            raise FailedPostCondition(f"The kpf stop kpfexpose2 command appears to have failed")
        time.sleep(2)

        log.warning('Stopping kpf_hk keyword service')
        cmd = ['kpf', 'stop', 'kpf_hk']
        result = subprocess.run(cmd, stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE)
        log.debug(f"  args: {result.args}")
        log.debug(f"  rtncode: {result.returncode}")
        log.debug(f"  STDOUT: {result.stdout.decode()}")
        log.debug(f"  STDERR: {result.stderr.decode()}")
        if result.returncode != 0:
            raise FailedPostCondition(f"The kpf stop kpf_hk command appears to have failed")
        time.sleep(2)
        # Get status response for log
        cmd = ['kpf', 'status', 'kpf_hk']
        result = subprocess.run(cmd, stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE)
        log.debug(f"  args: {result.args}")
        log.debug(f"  rtncode: {result.returncode}")
        log.debug(f"  STDOUT: {result.stdout.decode()}")
        log.debug(f"  STDERR: {result.stderr.decode()}")

        log.warning('Power cycling the Ca HK detector system')
        kpfpower = ktl.cache('kpfpower')
        outlets = [('J5', 'Andor Newton PS'),
                   ('J1', 'kpfexpose2 Galil RIO controller'),
                   ('J2', 'kpfexpose2 Galil output bank'),
                   ]
        for outlet_id, outlet_name in outlets:
            log.info(f"Powering off {outlet_id}: {outlet_name}")
            kpfpower[f'OUTLET_{outlet_id}'].write('Off')
        time.sleep(10)
        for outlet_id, outlet_name in outlets:
            log.info(f"Powering on {outlet_id}: {outlet_name}")
            kpfpower[f'OUTLET_{outlet_id}'].write('On')
            time.sleep(10)

        log.warning('Restarting kpf_hk keyword service')
        cmd = ['kpf', 'restart', 'kpf_hk']
        result = subprocess.run(cmd, stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE)
        log.debug(f"  args: {result.args}")
        log.debug(f"  rtncode: {result.returncode}")
        log.debug(f"  STDOUT: {result.stdout.decode()}")
        log.debug(f"  STDERR: {result.stderr.decode()}")
        if result.returncode != 0:
            raise FailedPostCondition(f"The kpf restart kpf_hk command appears to have failed")
        time.sleep(10)
        # Get status response for log
        cmd = ['kpf', 'status', 'kpf_hk']
        result = subprocess.run(cmd, stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE)
        log.debug(f"  args: {result.args}")
        log.debug(f"  rtncode: {result.returncode}")
        log.debug(f"  STDOUT: {result.stdout.decode()}")
        log.debug(f"  STDERR: {result.stderr.decode()}")

        log.warning('Restarting kpfexpose2 keyword service')
        cmd = ['kpf', 'restart', 'kpfexpose2']
        result = subprocess.run(cmd, stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE)
        log.debug(f"  args: {result.args}")
        log.debug(f"  rtncode: {result.returncode}")
        log.debug(f"  STDOUT: {result.stdout.decode()}")
        log.debug(f"  STDERR: {result.stderr.decode()}")
        if result.returncode != 0:
            raise FailedPostCondition(f"The kpf restart kpfexpose2 command appears to have failed")
        time.sleep(10)
        # Get status response for log
        cmd = ['kpf', 'status', 'kpfexpose2']
        result = subprocess.run(cmd, stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE)
        log.debug(f"  args: {result.args}")
        log.debug(f"  rtncode: {result.returncode}")
        log.debug(f"  STDOUT: {result.stdout.decode()}")
        log.debug(f"  STDERR: {result.stderr.decode()}")

        log.warning('Resetting Ca HK')
        ResetCaHKDetector.execute({})

    @classmethod
    def post_condition(cls, args):
        pass
