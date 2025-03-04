import time
from pathlib import Path
import subprocess

import ktl

from kpf import log, cfg
from kpf.exceptions import *
from kpf.KPFTranslatorFunction import KPFFunction, KPFScript
from kpf.guider.GuiderLastfile import GuiderLastfile


class DisplayGuiderContinuous(KPFFunction):
    '''Continuously display latest guider images to ds9 using `xpaset`.

    KTL Keywords Used:

    - `kpfguide.LASTFILE`
    '''
    @classmethod
    def pre_condition(cls, args):
        pass

    @classmethod
    def perform(cls, args):
        display_name = cfg.get('display', 'guider_xpa_target', fallback='CRED2')
        lastfile = ktl.cache('kpfguide', 'LASTFILE')
        initial_lastfile = lastfile.read()
        while True:
            expr = f"($kpfguide.LASTFILE != '{initial_lastfile}')"
            is_there_a_newfile = ktl.waitFor(expr, timeout=10)
            if is_there_a_newfile is True:
                initial_lastfile = lastfile.read()
                print(f"Displaying {initial_lastfile}")
                ds9cmd = ['xpaset', display_name, 'fits', f"{initial_lastfile}",
                          '<', f"{initial_lastfile}"]
#                 log.debug(f"Running: {' '.join(ds9cmd)}")
                subprocess.call(' '.join(ds9cmd), shell=True)
                regfile = Path(f'/home/kpfeng/fibers_on_cred2.reg')
                if regfile.exists() is True:
                    overlaycmd = ['xpaset', '-p', display_name, 'regions', 'file',
                                  f"{regfile}"]
#                     log.debug(f"Running: {' '.join(overlaycmd)}")
                    subprocess.call(' '.join(overlaycmd), shell=True)
        time.sleep(0.5)

    @classmethod
    def post_condition(cls, args):
        pass
