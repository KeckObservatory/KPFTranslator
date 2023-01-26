import ktl

import KPFTranslatorFunction
from .. import (log, KPFException, FailedPreCondition, FailedPostCondition,
                FailedToReachDestination, check_input)


class ControlAOHatch(KPFTranslatorFunction):
    '''Control the AO Hatch
    
    ARGS:
    destination - 'open' or 'close'
    '''
    @classmethod
    def pre_condition(cls, args, logger, cfg):
        check_input(args, 'destination', allowed_values=['close', 'closed', 'open'])
        return True

    @classmethod
    def perform(cls, args, logger, cfg):
        destination = args.get('destination', '').strip()
        ao = ktl.cache('ao')
        log.debug(f"Setting AO Hatch to {destination}")
        cmd = {'close': 1, 'closed': 1, 'open': 0}[destination]
        ao['aohatchcmd'].write(cmd)

    @classmethod
    def post_condition(cls, args, logger, cfg):
        destination = args.get('destination')
        final_dest = {'close': 'closed', 'closed': 'closed', 'open': 'open'}[destination]
        success = ktl.waitfor(f'($ao.AOHATCHSTS == {final_dest})', timeout=30)
        if success is not True:
            aohatchsts = ktl.cache('ao', 'AOHATCHSTS')
            raise FailedToReachDestination(aohatchsts.read(), final_dest)

    @classmethod
    def add_cmdline_args(cls, parser, cfg=None):
        '''The arguments to add to the command line interface.
        '''
        from collections import OrderedDict
        args_to_add = OrderedDict()
        args_to_add['destination'] = {'type': str,
                                'help': 'Desired hatch position: "open" or "close"'}

        parser = cls._add_args(parser, args_to_add, print_only=False)
        return super().add_cmdline_args(parser, cfg)
