import ktl

from kpf import log, cfg
from kpf.exceptions import *
from kpf.KPFTranslatorFunction import KPFFunction, KPFScript


class ControlAOHatch(KPFFunction):
    '''Command the AO Hatch to open or close.

    Args:
        destination (str): The destination position. Allowed Values: 'open' or
            'close'.

    KTL Keywords Used:

    - `ao.AOHATCHCMD`
    - `ao.AOHATCHSTS`
    '''
    @classmethod
    def pre_condition(cls, args):
        check_input(args, 'destination', allowed_values=['close', 'closed', 'open'])

    @classmethod
    def perform(cls, args):
        destination = args.get('destination', '').strip()
        ao = ktl.cache('ao')
        log.debug(f"Setting AO Hatch to {destination}")
        cmd = {'close': 1, 'closed': 1, 'open': 0}[destination]
        ao['aohatchcmd'].write(cmd)

    @classmethod
    def post_condition(cls, args):
        destination = args.get('destination', '').strip()
        final_dest = {'close': 'closed', 'closed': 'closed', 'open': 'open'}[destination]
        aohatchsts = ktl.cache('ao', 'AOHATCHSTS')
        success = aohatchsts.waitfor(f"== '{final_dest}'", timeout=30)
        if success is not True:
            raise FailedToReachDestination(aohatchsts.read(), final_dest)

    @classmethod
    def add_cmdline_args(cls, parser):
        parser.add_argument('destination', type=str,
                            choices=['open', 'close'],
                            help='Desired hatch position')
        return super().add_cmdline_args(parser)

