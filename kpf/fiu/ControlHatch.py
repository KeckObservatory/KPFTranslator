import ktl

from kpf import log, cfg
from kpf.exceptions import *
from kpf.KPFTranslatorFunction import KPFFunction, KPFScript


class ControlHatch(KPFFunction):
    '''Open or close the FIU hatch

    Args:
        destination (str): The desired FIU hatch position name. Allowed
            values: closed, open

    KTL Keywords Used:

    - `kpffiu.HATCH`
    '''
    @classmethod
    def pre_condition(cls, args):
        check_input(args, 'destination', allowed_values=['closed', 'open'])

    @classmethod
    def perform(cls, args):
        destination = args.get('destination', '').strip()
        HATCH = ktl.cache('kpffiu', 'HATCH')
        HATCH.write(destination)

    @classmethod
    def post_condition(cls, args):
        destination = args.get('destination', '').strip()
        timeout = cfg.getfloat('times', 'fiu_hatch_move_time', fallback=1)
        HATCH = ktl.cache('kpffiu', 'HATCH')
        if HATCH.waitFor(f'== "{destination}"', timeout=timeout) is not True:
            raise FailedToReachDestination(HATCH.read(), destination)

    @classmethod
    def add_cmdline_args(cls, parser):
        parser.add_argument('destination', type=str,
                            choices=['open', 'closed'],
                            help='Desired hatch position')
        return super().add_cmdline_args(parser)
