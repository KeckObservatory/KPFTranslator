import ktl

from KPFTranslatorFunction import KPFTranslatorFunction
from .. import (log, KPFException, FailedPreCondition, FailedPostCondition,
                FailedToReachDestination, check_input)


class SetGuiderGain(KPFTranslatorFunction):
    '''Set the guider gain via the kpfguide.GAIN keyword.
    
    ARGS:
    gain - The desired gain (high, medium, or low)
    '''
    @classmethod
    def pre_condition(cls, args, logger, cfg):
        check_input(args, 'GuideCamGain', allowed_values=['high', 'medium', 'low'])
        return True

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
        return success

    @classmethod
    def add_cmdline_args(cls, parser, cfg=None):
        '''The arguments to add to the command line interface.
        '''
        from collections import OrderedDict
        args_to_add = OrderedDict()
        args_to_add['GuideCamGain'] = {'type': str,
                                       'help': 'The requested gain.'}

        parser = cls._add_args(parser, args_to_add, print_only=False)
        return super().add_cmdline_args(parser, cfg)
