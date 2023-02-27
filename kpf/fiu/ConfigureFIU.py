import time
import ktl

from ddoitranslatormodule.KPFTranslatorFunction import KPFTranslatorFunction
from .. import (log, KPFException, FailedPreCondition, FailedPostCondition,
                FailedToReachDestination, check_input)
from .WaitForConfigureFIU import WaitForConfigureFIU


##-----------------------------------------------------------------------------
## Configure FIU Once
##-----------------------------------------------------------------------------
class ConfigureFIUOnce(KPFTranslatorFunction):
    '''Set the FIU mode (kpffiu.MODE) with a single attempt
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
        log.debug(f"Setting FIU mode to {dest}")
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
            if dest.lower() not in modes.lower().split(','):
                raise FailedToReachDestination(dest, modes)


##-----------------------------------------------------------------------------
## Configure FIU
##-----------------------------------------------------------------------------
class ConfigureFIU(KPFTranslatorFunction):
    '''Set the FIU mode (kpffiu.MODE). This will retry if the first attempt
    fails.
    
    ARGS:
    mode - The desired FIU mode
    wait (bool) - Wait for move to complete before returning? (default: True)
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
        try:
            ConfigureFIUOnce.execute({'mode': dest,
                                      'wait': args.get('wait', True)})
        except FailedToReachDestination:
            log.warning(f'FIU failed to reach destination. Retrying.')
            shim_time = cfg.get('times', 'fiu_mode_shim_time', fallback=0.5)
            time.sleep(shim_time)
            ConfigureFIUOnce.execute({'mode': dest,
                                      'wait': args.get('wait', True)})

    @classmethod
    def post_condition(cls, args, logger, cfg):
        if args.get('wait', True) is True:
            WaitForConfigureFIU.execute(args)
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
