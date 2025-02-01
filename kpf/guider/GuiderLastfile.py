from pathlib import Path

import ktl

from kpf import log, cfg, check_input
from kpf.exceptions import *
from kpf.KPFTranslatorFunction import KPFFunction, KPFScript


class GuiderLastfile(KPFFunction):
    '''Print the value of the kpfguide.LASTFILE keyword to STDOUT

    Args:
        wait (bool): Return only after lastfile is updated? (default = False)

    KTL Keywords Used:

    - `kpfguide.LASTFILE`
    '''
    @classmethod
    def pre_condition(cls, args):
        pass

    @classmethod
    def perform(cls, args):
        kpfguide = ktl.cache('kpfguide')
        if args.get('wait', True) is True:
            exptime = kpfguide['EXPTIME'].read(binary=True)
            initial_lastfile = kpfguide['LASTFILE'].read()
            timeout = cfg.getfloat('times', 'kpfguide_shim_time', fallback=0.01)
            expr = f"($kpfguide.LASTFILE != '{initial_lastfile}')"
            ktl.waitFor(expr, timeout=exptime+timeout)
        lastfile = kpfguide['LASTFILE'].read()
        print(lastfile)
        return lastfile

    @classmethod
    def post_condition(cls, args):
        pass

    @classmethod
    def add_cmdline_args(cls, parser):
        parser.add_argument("--nowait", dest="wait",
                            default=True, action="store_false",
                            help="Send exposure command and return immediately?")
        return super().add_cmdline_args(parser)
