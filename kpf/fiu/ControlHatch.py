import ktl

from kpf import log, cfg, check_input
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
        kpffiu = ktl.cache('kpffiu')
        kpffiu['HATCH'].write(destination)

    @classmethod
    def post_condition(cls, args):
        destination = args.get('destination', '').strip()
        timeout = cfg.getfloat('times', 'fiu_hatch_move_time', fallback=1)
        success = ktl.waitFor(f'($kpffiu.hatch == {destination})', timeout=timeout)
        if success is not True:
            hatch = ktl.cache('kpffiu', 'HATCH')
            raise FailedToReachDestination(hatch.read(), destination)

    @classmethod
    def add_cmdline_args(cls, parser):
        parser.add_argument('destination', type=str,
                            choices=['open', 'closed'],
                            help='Desired hatch position')
        return super().add_cmdline_args(parser)
