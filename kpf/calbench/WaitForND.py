import ktl

from kpf import log, cfg, check_input
from kpf.exceptions import *
from kpf.KPFTranslatorFunction import KPFFunction, KPFScript
from kpf.calbench.WaitForND1 import WaitForND1
from kpf.calbench.WaitForND2 import WaitForND2


class WaitForND(KPFFunction):
    '''Wait for both ND filter wheels.

    Args:
        CalND1 (str): The neutral density filter to put in the first filter
            wheel. This affects both the simultaneous calibration light and
            light which can be routed through the FIU to the science and sky
            fibers. Allowed Values: `OD 0.1`, `OD 1.0`, `OD 1.3`, `OD 2.0`,
            `OD 3.0`, `OD 4.0`
        CalND2 (str): The neutral density filter to put in the first filter
            wheel. This affects only the light injected in to the simultaneous
            calibration fiber. Allowed Values: `OD 0.1`, `OD 0.3`, `OD 0.5`,
            `OD 0.8`, `OD 1.0`, `OD 4.0`

    Functions Called:

    - `kpf.calbench.WaitForND1`
    - `kpf.calbench.WaitForND2`
    '''
    @classmethod
    def pre_condition(cls, args):
        pass

    @classmethod
    def perform(cls, args):
        WaitForND1.execute(args)
        WaitForND2.execute(args)

    @classmethod
    def post_condition(cls, args):
        pass

    @classmethod
    def add_cmdline_args(cls, parser):
        parser.add_argument('CalND1', type=str,
                            choices=["OD 0.1", "OD 1.0", "OD 1.3", "OD 2.0",
                                     "OD 3.0", "OD 4.0"],
                            help='ND1 Filter to use.')
        parser.add_argument('CalND2', type=str,
                            help='ND2 Filter to use.')
        return super().add_cmdline_args(parser)

