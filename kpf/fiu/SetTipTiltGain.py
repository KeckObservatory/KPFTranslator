import ktl

from kpf.KPFTranslatorFunction import KPFTranslatorFunction
from kpf import (log, KPFException, FailedPreCondition, FailedPostCondition,
                 FailedToReachDestination, check_input)


class SetTipTiltGain(KPFTranslatorFunction):
    '''Set the CRED2 camera gain
    
    ARGS:
    =====
    :GuideLoopGain: The desired gain value
    '''
    @classmethod
    def pre_condition(cls, args, logger, cfg):
        check_input(args, 'GuideLoopGain', value_min=0, value_max=1)
        return True

    @classmethod
    def perform(cls, args, logger, cfg):
        gain = float(args.get('GuideLoopGain'))
        tiptiltgain = ktl.cache('kpfguide', 'TIPTILT_GAIN')
        tiptiltgain.write(gain)

    @classmethod
    def post_condition(cls, args, logger, cfg):
        gain = float(args.get('GuideLoopGain'))
        timeout = cfg.getfloat('times', 'tip_tilt_move_time', fallback=0.1)
        tol = cfg.getfloat('tolerances', 'tip_tilt_gain_tolerance', fallback=0.001)
        expr = (f"($kpfguide.TIPTILT_GAIN >= {gain-tol}) and "
                f"($kpfguide.TIPTILT_GAIN <= {gain+tol})")
        success = ktl.waitFor(expr, timeout=timeout)
        if success is not True:
            tiptiltgain = ktl.cache('kpfguide', 'TIPTILT_GAIN')
            raise FailedToReachDestination(tiptiltgain.read(), gain)
        return success

    @classmethod
    def add_cmdline_args(cls, parser, cfg=None):
        '''The arguments to add to the command line interface.
        '''
        from collections import OrderedDict
        args_to_add = OrderedDict()
        args_to_add['GuideLoopGain'] = {'type': float,
                                        'help': 'Tip tilt control loop gain'}
        parser = cls._add_args(parser, args_to_add, print_only=False)
        return super().add_cmdline_args(parser, cfg)
