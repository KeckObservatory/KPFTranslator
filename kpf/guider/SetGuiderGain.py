import ktl

from kpf.KPFTranslatorFunction import KPFTranslatorFunction
from kpf import (log, KPFException, FailedPreCondition, FailedPostCondition,
                 FailedToReachDestination, check_input)


class SetGuiderGain(KPFTranslatorFunction):
    '''Set the guider gain via the kpfguide.GAIN keyword.

    Args:
        GuideCamGain (str): The desired gain. Allowed values: high, medium, or
            low.

    KTL Keywords Used:

    - `kpfguide.GAIN`
    '''
    @classmethod
    def pre_condition(cls, args, logger, cfg):
        check_input(args, 'GuideCamGain', allowed_values=['high', 'medium', 'low'])

    @classmethod
    def perform(cls, args, logger, cfg):
        gainkw = ktl.cache('kpfguide', 'GAIN')
        gain = args.get('GuideCamGain')
        log.debug(f'Setting guider gain to {gain}')
        gainkw.write(gain)

    @classmethod
    def post_condition(cls, args, logger, cfg):
        gainkw = ktl.cache('kpfguide', 'GAIN')
        gain = args.get('GuideCamGain')
        expr = (f"($kpfguide.GAIN == '{gain}')")
        success = ktl.waitFor(expr, timeout=1)
        if not success:
            raise FailedToReachDestination(gainkw.read(), gain)

    @classmethod
    def add_cmdline_args(cls, parser, cfg=None):
        parser.add_argument('GuideCamGain', type=str,
                            choices=['high', 'medium', 'low'],
                            help='The gain')
        return super().add_cmdline_args(parser, cfg)
