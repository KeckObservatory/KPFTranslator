import time
import ktl

from ddoitranslatormodule.KPFTranslatorFunction import KPFTranslatorFunction
from .. import (log, KPFException, FailedPreCondition, FailedPostCondition,
                FailedToReachDestination, check_input)
from .WaitForConfigureFIU import WaitForConfigureFIU


class ConfigureFIU(KPFTranslatorFunction):
    '''Set the FIU mode (kpffiu.MODE)
    
    Values: 0 None 1 Stowed 2 Alignment 3 Acquisition 4 Observing 5 Calibration
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
        kpffiu['MODE'].write(dest, wait=args.get('wait', True))
        shim_time = cfg.get('times', 'fiu_mode_shim_time', fallback=0.5)
        time.sleep(shim_time)

    @classmethod
    def post_condition(cls, args, logger, cfg):
        if args.get('wait', True) is True:
            WaitForConfigureFIU.execute(args)
            dest = args.get('mode')
            kpffiu = ktl.cache('kpffiu')
            modes = kpffiu['MODE'].read()
            if dest not in modes.split(','):
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
