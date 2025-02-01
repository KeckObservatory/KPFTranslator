import ktl

from kpf import log, cfg, check_input
from kpf.exceptions import *
from kpf.KPFTranslatorFunction import KPFFunction, KPFScript


class SetGuiderGain(KPFFunction):
    '''Set the guider gain via the kpfguide.GAIN keyword.

    Args:
        GuideCamGain (str): The desired gain. Allowed values: high, medium, or
            low.

    KTL Keywords Used:

    - `kpfguide.GAIN`
    '''
    @classmethod
    def pre_condition(cls, args):
        check_input(args, 'GuideCamGain', allowed_values=['high', 'medium', 'low'])

    @classmethod
    def perform(cls, args):
        gainkw = ktl.cache('kpfguide', 'GAIN')
        gain = args.get('GuideCamGain')
        log.debug(f'Setting guider gain to {gain}')
        gainkw.write(gain)

    @classmethod
    def post_condition(cls, args):
        gainkw = ktl.cache('kpfguide', 'GAIN')
        gain = args.get('GuideCamGain')
        expr = (f"($kpfguide.GAIN == '{gain}')")
        success = ktl.waitFor(expr, timeout=1)
        if not success:
            raise FailedToReachDestination(gainkw.read(), gain)

    @classmethod
    def add_cmdline_args(cls, parser):
        parser.add_argument('GuideCamGain', type=str,
                            choices=['high', 'medium', 'low'],
                            help='The gain')
        return super().add_cmdline_args(parser)
