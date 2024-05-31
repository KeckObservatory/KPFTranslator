import ktl

from kpf.KPFTranslatorFunction import KPFTranslatorFunction
from kpf import (log, KPFException, FailedPreCondition, FailedPostCondition,
                 FailedToReachDestination, check_input)
from kpf.calbench.SetND1 import SetND1
from kpf.calbench.SetND2 import SetND2


class SetND(KPFTranslatorFunction):
    '''# Description
    Set the filter in the ND1 & ND2 filter wheels via the `kpfcal.ND1POS` and
    `kpfcal.ND2POS` keywords.

    # Parameters

    **CalND1** (`str`)
    > The neutral density filter to put in the first filter
    wheel. This affects both the simultaneous calibration light and light
    which can be routed through the FIU to the science and sky fibers.
    <br>Allowed Values: `OD 0.1`, `OD 1.0`, `OD 1.3`, `OD 2.0`, `OD 3.0`, `OD 4.0`

    **CalND2** (`str`)
    > The neutral density filter to put in the second filter
    wheel. This affects only the light injected in to the simultaneous
    calibration fiber.
    <br>Allowed Values: `OD 0.1`, `OD 0.3`, `OD 0.5`, `OD 0.8`, `OD 1.0`, `OD 4.0`

    **wait** (`bool`)
    > Wait for move to complete before returning?
    <br>default: True
    '''
    @classmethod
    def pre_condition(cls, args, logger, cfg):
        pass

    @classmethod
    def perform(cls, args, logger, cfg):
        SetND1.execute(args)
        SetND2.execute(args)

    @classmethod
    def post_condition(cls, args, logger, cfg):
        pass

    @classmethod
    def add_cmdline_args(cls, parser, cfg=None):
        parser.add_argument('CalND1', type=str,
                            choices=["OD 0.1", "OD 1.0", "OD 1.3", "OD 2.0",
                                     "OD 3.0", "OD 4.0"],
                            help='ND1 Filter to use.')
        parser.add_argument('CalND2', type=str,
                            choices=["OD 0.1", "OD 0.3", "OD 0.5", "OD 0.8",
                                     "OD 1.0", "OD 4.0"],
                            help='ND2 Filter to use.')
        parser.add_argument("--nowait", dest="wait",
                            default=True, action="store_false",
                            help="Send move and return immediately?")
        return super().add_cmdline_args(parser, cfg)

