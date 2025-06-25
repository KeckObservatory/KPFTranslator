from pathlib import Path
import subprocess

import ktl

from kpf import log, cfg
from kpf.exceptions import *
from kpf.KPFTranslatorFunction import KPFFunction, KPFScript


class TakeFVCExposure(KPFFunction):
    '''Take an exposure with the specified fiber viewing camera

    Args:
        camera (str): Which FVC camera? Allowed values: SCI, CAHK, EXT, CAL
        wait (bool): Wait for image to complete before returning? (default: True)
        display (bool): Display the resulting image to the engineering ds9
              instance for FVCs using XPA?

    KTL Keywords Used:

    - `kpffvc.SCIEXPTIME`
    - `kpffvc.CAHKEXPTIME`
    - `kpffvc.EXTEXPTIME`
    - `kpffvc.CALEXPTIME`
    - `kpffvc.SCILASTFILE`
    - `kpffvc.CALLASTFILE`
    - `kpffvc.EXTLASTFILE`
    - `kpffvc.CAHKLASTFILE`
    - `kpffvc.SCIEXPOSE`
    - `kpffvc.CALEXPOSE`
    - `kpffvc.EXTEXPOSE`
    - `kpffvc.CAHKEXPOSE`
    - `kpfpower.KPFFVC1`
    - `kpfpower.KPFFVC2`
    - `kpfpower.KPFFVC3`
    '''
    @classmethod
    def pre_condition(cls, args):
        check_input(args, 'camera', allowed_values=['SCI', 'CAHK', 'CAL', 'EXT'])
        # Check if power is on
        camera = args.get('camera')
        camnum = {'SCI': 1, 'CAHK': 2, 'CAL': 3, 'EXT': None}[camera]
        if camnum is not None:
            powerkw = ktl.cache('kpfpower', f"KPFFVC{camnum}")
            if powerkw.read() != 'On':
                raise FailedPreCondition(f"{camera}FVC power is not On")

    @classmethod
    def perform(cls, args):
        camera = args.get('camera')
        kpffvc = ktl.cache('kpffvc')
        exptime = kpffvc[f'{camera}EXPTIME'].read(binary=True)
        lastfile = kpffvc[f'{camera}LASTFILE']
        initial_lastfile = lastfile.read()
        wait = args.get('wait', True)
        kpffvc[f'{camera}EXPOSE'].write('yes', wait=wait)
        if wait is True:
            timeout = cfg.getfloat('times', 'fvc_command_timeout', fallback=5)
            expr = f"($kpffvc.{camera}LASTFILE != '{initial_lastfile}')"
            ktl.waitFor(expr, timeout=exptime+timeout)
        if wait is True and args.get('display', False) is True:
            display_name = cfg.get('display', 'fvc_xpa_target', fallback='FVC')
            ds9cmd = ['xpaset', display_name, 'fits', f"{lastfile.read()}",
                      '<', f"{lastfile.read()}"]
            log.debug(f"Running: {' '.join(ds9cmd)}")
            subprocess.call(' '.join(ds9cmd), shell=True)
            regfile = Path(f'/home/kpfeng/fibers_on_{camera.lower()}fvc.reg')
            if regfile.exists() is True:
                overlaycmd = ['xpaset', '-p', display_name, 'regions', 'file',
                              f"{regfile}"]
                log.debug(f"Running: {' '.join(overlaycmd)}")
                subprocess.call(' '.join(overlaycmd), shell=True)
        return kpffvc[f"{camera}LASTFILE"].read()

    @classmethod
    def post_condition(cls, args):
        camera = args.get('camera', 'SCI')
        kpffvc = ktl.cache('kpffvc')
        lastfile = kpffvc[f'{camera}LASTFILE']
        lastfile.monitor()
        new_file = Path(f"{lastfile}")
        log.debug(f"{camera}FVC LASTFILE: {new_file}")
        if new_file.exists() == False:
            raise FailedPostCondition(f'Output file not found: {new_file}')

    @classmethod
    def add_cmdline_args(cls, parser):
        parser.add_argument('camera', type=str,
                            choices=['SCI', 'CAHK', 'CAL', 'EXT'],
                            help='The FVC camera')
        parser.add_argument("--nowait", dest="wait",
                            default=True, action="store_false",
                            help="Send exposure command and return immediately?")
        parser.add_argument("--display", dest="display",
                            default=False, action="store_true",
                            help="Display image via engineering ds9?")
        return super().add_cmdline_args(parser)
