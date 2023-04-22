import ktl

from kpf.KPFTranslatorFunction import KPFTranslatorFunction
from kpf import (log, KPFException, FailedPreCondition, FailedPostCondition,
                 FailedToReachDestination, check_input)
from kpf.calbench.SetND1 import SetND1
from kpf.calbench.SetND2 import SetND2


class SetND(KPFTranslatorFunction):
    '''Set the filter in the ND1 & ND2 filter wheels via the `kpfcal.ND1POS`
    and `kpfcal.ND2POS` keywords.
    
    Allowed Values:
    ND1: "OD 0.1", "OD 1.0", "OD 1.3", "OD 2.0", "OD 3.0", "OD 4.0"
    ND2: "OD 0.1", "OD 0.3", "OD 0.5", "OD 0.8", "OD 1.0", "OD 4.0"
    
    ARGS:
    =====
    :CalND1: The neutral density filter to put in the first filter wheel.
    :CalND2: The neutral density filter to put in the second filter wheel.
    :wait: (bool) Wait for move to complete before returning? (default: True)
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
        '''The arguments to add to the command line interface.
        '''
        from collections import OrderedDict
        args_to_add = OrderedDict()
        args_to_add['CalND1'] = {'type': str,
                                 'help': 'ND1 Filter to use'}
        args_to_add['CalND2'] = {'type': str,
                                 'help': 'ND2 Filter to use'}
        parser = cls._add_args(parser, args_to_add, print_only=False)

        parser = cls._add_bool_arg(parser, 'wait',
            'Return only after move is finished?', default=True)

        return super().add_cmdline_args(parser, cfg)

