import ktl

from kpf import log, cfg
from kpf.exceptions import *
from kpf.KPFTranslatorFunction import KPFFunction, KPFScript


class SetFlatFieldFiberPos(KPFFunction):
    '''# Description
    Set the flat field fiber aperture via the `kpfcal.FF_FIBERPOS` keyword.

    Args:
        FF_FiberPos (str): The name of the flat field fiber position desired.
            Allowed Values: "Blank", "6 mm f/5", "7.5 mm f/4", "10 mm f/3",
            "13.2 mm f/2.3", "Open".
        wait (bool): Wait for move to complete before returning? default: True

    KTL Keywords Used

    - `kpfcal.FF_FIBERPOS`
    '''
    @classmethod
    def pre_condition(cls, args):
        FF_FIBERPOS = ktl.cache('kpfcal', 'FF_FIBERPOS')
        allowed_values = list(FF_FIBERPOS._getEnumerators())
        if 'Unknown' in allowed_values:
            allowed_values.pop(allowed_values.index('Unknown'))
        check_input(args, 'FF_FiberPos', allowed_values=allowed_values)

    @classmethod
    def perform(cls, args):
        target = args.get('FF_FiberPos')
        log.debug(f"Setting FF_FiberPos to {target}")
        FF_FIBERPOS = ktl.cache('kpfcal', 'FF_FIBERPOS')
        FF_FIBERPOS.write(target, wait=args.get('wait', True))

    @classmethod
    def post_condition(cls, args):
        target = args.get('FF_FiberPos')
        timeout = cfg.getfloat('times', 'nd_move_time', fallback=20)
        FF_FIBERPOS = ktl.cache('kpfcal', 'FF_FIBERPOS')
        if FF_FIBERPOS.waitFor(f"== '{target}'", timeout=timeout) is not True:
            raise FailedToReachDestination(FF_FIBERPOS.read(), target)

    @classmethod
    def add_cmdline_args(cls, parser):
        parser.add_argument('FF_FiberPos', type=str,
                            choices=["Blank", "6 mm f/5", "7.5 mm f/4",
                                     "10 mm f/3", "13.2 mm f/2.3", "Open"],
                            help='Wide flat aperture to use.')
        parser.add_argument("--nowait", dest="wait",
                            default=True, action="store_false",
                            help="Send move and return immediately?")
        return super().add_cmdline_args(parser)
