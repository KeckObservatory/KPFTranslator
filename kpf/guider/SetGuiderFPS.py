import ktl

from kpf.KPFTranslatorFunction import KPFTranslatorFunction
from kpf import (log, KPFException, FailedPreCondition, FailedPostCondition,
                 FailedToReachDestination, check_input)


class SetGuiderFPS(KPFTranslatorFunction):
    '''Set the guider FPS (frames per second) via the kpfguide.FPS
    keyword.
    
    ARGS:
    =====
    :fps: Number of frames per second
    '''
    @classmethod
    def pre_condition(cls, args, logger, cfg):
        check_input(args, 'GuideFPS', value_min=0.0001, value_max=400)
        return True

    @classmethod
    def perform(cls, args, logger, cfg):
        fpskw = ktl.cache('kpfguide', 'FPS')
        fps = args.get('GuideFPS')
        log.debug(f'Setting guider FPS to {fps}')
        fpskw.write(fps)

    @classmethod
    def post_condition(cls, args, logger, cfg):
        fpstol = cfg.getfloat('tolerances', 'guider_fps_tolerance', fallback=0.01)
        fpskw = ktl.cache('kpfguide', 'FPS')
        fps = args.get('GuideFPS')
        expr = (f'($kpfguide.FPS >= {fps-fpstol}) and '\
                f'($kpfguide.FPS <= {fps+fpstol})')
        success = ktl.waitFor(expr, timeout=1)
        if not success:
            raise FailedToReachDestination(fpskw.read(), fps)

    @classmethod
    def add_cmdline_args(cls, parser, cfg=None):
        '''The arguments to add to the command line interface.
        '''
        parser.add_argument('GuideFPS', type=float,
                            help='The frames per second (FPS)')
        return super().add_cmdline_args(parser, cfg)
