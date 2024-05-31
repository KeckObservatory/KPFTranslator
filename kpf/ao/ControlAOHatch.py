import ktl

from kpf.KPFTranslatorFunction import KPFTranslatorFunction
from kpf import (log, KPFException, FailedPreCondition, FailedPostCondition,
                 FailedToReachDestination, check_input)


class ControlAOHatch(KPFTranslatorFunction):
    '''Control the AO Hatch
    
    ARGS:
    =====
    :destination: 'open' or 'close'
    '''
    @classmethod
    def pre_condition(cls, args, logger, cfg):
        check_input(args, 'destination', allowed_values=['close', 'closed', 'open'])

    @classmethod
    def perform(cls, args, logger, cfg):
        destination = args.get('destination', '').strip()
        ao = ktl.cache('ao')
        log.debug(f"Setting AO Hatch to {destination}")
        cmd = {'close': 1, 'closed': 1, 'open': 0}[destination]
        ao['aohatchcmd'].write(cmd)

    @classmethod
    def post_condition(cls, args, logger, cfg):
        destination = args.get('destination', '').strip()
        final_dest = {'close': 'closed', 'closed': 'closed', 'open': 'open'}[destination]
        aohatchsts = ktl.cache('ao', 'AOHATCHSTS')
        success = aohatchsts.waitfor(f"== '{final_dest}'", timeout=30)
        if success is not True:
            raise FailedToReachDestination(aohatchsts.read(), final_dest)

    @classmethod
    def add_cmdline_args(cls, parser, cfg=None):
        parser.add_argument('destination', type=str,
                            choices=['open', 'close'],
                            help='Desired hatch position')
        return super().add_cmdline_args(parser, cfg)

