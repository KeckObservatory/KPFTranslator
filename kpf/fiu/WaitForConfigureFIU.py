import ktl
from time import sleep
from datetime import datetime, timedelta

from kpf.KPFTranslatorFunction import KPFTranslatorFunction
from .. import (log, KPFException, FailedPreCondition, FailedPostCondition,
                FailedToReachDestination, check_input)


class WaitForConfigureFIU(KPFTranslatorFunction):
    '''Wait for the FIU to reach specified mode (kpffiu.MODE)
    
    Values: 0 None 1 Stowed 2 Alignment 3 Acquisition 4 Observing 5 Calibration
    
    ARGS:
    mode - The desired FIU mode
    '''
    @classmethod
    def pre_condition(cls, args, logger, cfg):
        keyword = ktl.cache('kpffiu', 'MODE')
        allowed_values = list(keyword._getEnumerators())
        if 'None' in allowed_values:
            allowed_values.pop(allowed_values.index('None'))
        check_input(args, 'mode', allowed_values=allowed_values)
        return True

    @classmethod
    def perform(cls, args, logger, cfg):
        dest = args.get('mode')
        kpffiu = ktl.cache('kpffiu')
        modes = kpffiu['MODE'].read()
        start = datetime.utcnow()
        move_times = [cfg.get('times', 'fiu_fold_mirror_move_time', fallback=30),
                      cfg.get('times', 'fiu_hatch_move_time', fallback=2)]
        end = start + timedelta(seconds=max(move_times))
        while dest.lower() not in modes.lower().split(',') and datetime.utcnow() <= end:
            sleep(1)
            modes = kpffiu['MODE'].read()

    @classmethod
    def post_condition(cls, args, logger, cfg):
        dest = args.get('mode')
        kpffiu = ktl.cache('kpffiu')
        modes = kpffiu['MODE'].read()
        if dest.lower() not in modes.lower().split(','):
            raise FailedToReachDestination(dest, modes)

    @classmethod
    def add_cmdline_args(cls, parser, cfg=None):
        '''The arguments to add to the command line interface.
        '''
        from collections import OrderedDict
        args_to_add = OrderedDict()
        args_to_add['mode'] = {'type': str,
                               'help': 'Desired mode (see kpffiu.MODE)'}
        parser = cls._add_args(parser, args_to_add, print_only=False)

        parser = cls._add_bool_arg(parser, 'wait',
            'Return only after move is finished?', default=True)

        return super().add_cmdline_args(parser, cfg)

