import ktl

from ddoitranslatormodule.KPFTranslatorFunction import KPFTranslatorFunction
from .. import (log, KPFException, FailedPreCondition, FailedPostCondition,
                FailedToReachDestination, check_input)


class ControlAOHatch(KPFTranslatorFunction):
    '''Control the AO Hatch
    
    ARGS:
    destination - 'open' or 'close'
    '''
    @classmethod
    def pre_condition(cls, args, logger, cfg):
        check_input(args, 'destination', allowed_values=['close', 'open'])
        return True

    @classmethod
    def perform(cls, args, logger, cfg):
        destination = args.get('destination', '').strip()
        ao = ktl.cache('ao')
        log.debug(f"Setting AO Hatch to {destination}")
        ao['aohatchcmd'].write(destination)

    @classmethod
    def post_condition(cls, args, logger, cfg):
        destination = args.get('destination')
        success = ktl.waitfor(f'($ao.AOHATCHSTS == {destination})', timeout=30)
        if success is not True:
            aohatchsts = ktl.cache('ao', 'AOHATCHSTS')
            raise FailedPostCondition(aohatchsts.read(), destination)

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
