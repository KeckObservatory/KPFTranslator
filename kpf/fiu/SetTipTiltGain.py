import ktl

from ddoitranslatormodule.KPFTranslatorFunction import KPFTranslatorFunction


class SetTipTiltGain(KPFTranslatorFunction):
    '''
    '''
    @classmethod
    def pre_condition(cls, args, logger, cfg):
        gain = args.get('gain', None)
        if gain is None:
            return False
        gain = float(gain)
        return (gain > 0) and (gain <= 1)

    @classmethod
    def perform(cls, args, logger, cfg):
        gain = float(args.get('gain'))
        tiptiltgain = ktl.cache('kpfguide', 'TIPTILT_GAIN')
        tiptiltgain.write(gain)

    @classmethod
    def post_condition(cls, args, logger, cfg):
        gain = float(args.get('gain'))
        cfg = cls._load_config(cls, cfg)
        timeout = cfg.get('times', 'tip_tilt_move_time', fallback=0.1)
        tol = cfg.get('tolerances', 'tip_tilt_gain_tolerance', fallback=0.001)
        expr = (f"($kpfguide.TIPTILT_GAIN >= {gain-tol}) and "
                f"($kpfguide.TIPTILT_GAIN <= {gain+tol})")
        success = ktl.waitFor(expr, timeout=timeout)
        return success

    @classmethod
    def add_cmdline_args(cls, parser, cfg=None):
        '''The arguments to add to the command line interface.
        '''
        from collections import OrderedDict
        args_to_add = OrderedDict()
        args_to_add['gain'] = {'type': float,
                               'help': 'Tip tilt control loop gain'}
        parser = cls._add_args(parser, args_to_add, print_only=False)
        return super().add_cmdline_args(parser, cfg)
