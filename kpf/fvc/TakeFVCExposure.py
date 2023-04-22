from pathlib import Path
import subprocess

import ktl

from kpf.KPFTranslatorFunction import KPFTranslatorFunction
from kpf import (log, KPFException, FailedPreCondition, FailedPostCondition,
                 FailedToReachDestination, check_input)


class TakeFVCExposure(KPFTranslatorFunction):
    '''Take an exposure with the specified fiber viewing camera
    
    ARGS:
    =====
    :camera: Which FVC camera (SCI, CAHK, EXT, CAL)?
    :wait: (bool) Wait for move to complete before returning? (default: True)
    :display: (bool) Display the resulting image to the engineering ds9
              instance for FVCs using XPA.
    '''
    @classmethod
    def pre_condition(cls, args, logger, cfg):
        check_input(args, 'camera', allowed_values=['SCI', 'CAHK', 'CAL', 'EXT'])

    @classmethod
    def perform(cls, args, logger, cfg):
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

    @classmethod
    def post_condition(cls, args, logger, cfg):
        camera = args.get('camera', 'SCI')
        kpffvc = ktl.cache('kpffvc')
        lastfile = kpffvc[f'{camera}LASTFILE']
        lastfile.monitor()
        new_file = Path(f"{lastfile}")
        log.debug(f"{camera}FVC LASTFILE: {new_file}")
        if new_file.exists() == False:
            raise FailedPostCondition(f'Output file not found: {new_file}')

    @classmethod
    def add_cmdline_args(cls, parser, cfg=None):
        '''The arguments to add to the command line interface.
        '''
        parser.add_argument('camera', type=str,
                            help='The FVC camera (SCI, CAHK, CAL)')
        parser.add_argument("--nowait", dest="wait",
                            default=True, action="store_false",
                            help="Send exposure command and return immediately?")
        parser.add_argument("--display", dest="display",
                            default=False, action="store_true",
                            help="Display image via engineering ds9?")
        return super().add_cmdline_args(parser, cfg)
