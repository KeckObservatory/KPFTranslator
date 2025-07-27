import ktl

from kpf import log, cfg
from kpf.exceptions import *
from kpf.KPFTranslatorFunction import KPFFunction, KPFScript


class ControlFoldMirror(KPFFunction):
    '''Insert or remove the FIU Cal Fold Mirror from the beam.

    Args:
        destination (str): The desired FIU fold mirror position name. Allowed
            values: in, out
        wait (bool): Wait for move to complete before returning? (default: True)

    KTL Keywords Used:

    - `kpffiu.FOLDNAM`
    '''
    @classmethod
    def pre_condition(cls, args):
        destination = args.get('destination', '').strip()
        if destination.lower() not in ['in', 'out']:
            raise FailedPreCondition(f"Requested state {destination} is invalid")

    @classmethod
    def perform(cls, args):
        destination = args.get('destination', '').strip()
        FOLDNAM = ktl.cache('kpffiu', 'FOLDNAM')
        FOLDNAM.write(destination)

    @classmethod
    def post_condition(cls, args):
        destination = args.get('destination', '').strip()
        timeout = cfg.getfloat('times', 'fiu_fold_mirror_move_time', fallback=5)
        FOLDNAM = ktl.cache('kpffiu', 'FOLDNAM')
        if FOLDNAM.waitFor(f'== "{destination}"', timeout=timeout) is not True:
            raise FailedToReachDestination(FOLDNAM.read(), destination)

    @classmethod
    def add_cmdline_args(cls, parser):
        parser.add_argument('destination', type=str,
                            choices=['in', 'out'],
                            help='Desired fold mirror position')
        return super().add_cmdline_args(parser)

