import ktl

from kpf.KPFTranslatorFunction import KPFTranslatorFunction
from kpf import (log, KPFException, FailedPreCondition, FailedPostCondition,
                 FailedToReachDestination, check_input)
from kpf.calbench.WaitForND1 import WaitForND1
from kpf.calbench.WaitForND2 import WaitForND2


class WaitForND1(KPFTranslatorFunction):
    '''Wait for the ND1 filter wheel (the one at the output of the 
    octagon) via the `kpfcal.ND1POS` keyword.
    
    Allowed Values:
    "OD 0.1", "OD 1.0", "OD 1.3", "OD 2.0", "OD 3.0", "OD 4.0"
    
    ARGS:
    =====
    :CalND1: The neutral density filter to put in the first filter wheel.
        Allowed values are "OD 0.1", "OD 1.0", "OD 1.3", "OD 2.0", "OD 3.0",
        "OD 4.0"
    :CalND2: The neutral density filter to put in the second filter wheel.
        Allowed values are "OD 0.1", "OD 0.3", "OD 0.5", "OD 0.8", "OD 1.0",
        "OD 4.0"
    '''
    @classmethod
    def pre_condition(cls, args, logger, cfg):
        pass

    @classmethod
    def perform(cls, args, logger, cfg):
        WaitForND1.execute(args)
        WaitForND2.execute(args)

    @classmethod
    def post_condition(cls, args, logger, cfg):
        pass

    @classmethod
    def add_cmdline_args(cls, parser, cfg=None):
        '''The arguments to add to the command line interface.
        '''
        parser.add_argument('CalND1', type=str,
                            choices=["OD 0.1", "OD 1.0", "OD 1.3", "OD 2.0",
                                     "OD 3.0", "OD 4.0"],
                            help='ND1 Filter to use.')
        parser.add_argument('CalND2', type=str,
                            help='ND2 Filter to use.')
        return super().add_cmdline_args(parser, cfg)

