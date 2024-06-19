from kpf.KPFTranslatorFunction import KPFTranslatorFunction
from kpf import (log, KPFException, FailedPreCondition, FailedPostCondition,
                 FailedToReachDestination, check_input)
from kpf.guider.SetGuiderGain import SetGuiderGain
from kpf.guider.SetGuiderFPS import SetGuiderFPS


# Engineering OBs (not consistent)
# Jmag, Gain
# 4.37, low
# 2.14, low
# 4.45, low
# 4.29, low
# 6.13, low
# 4.88, low
# 4.48, low
# 5.93, low
# 3.3, low
# 4.48, low
# 9, medium
# 10, medium
# 7.5, low
# 2.4, low
# 8.4, high

class PredictGuiderParameters(KPFTranslatorFunction):
    '''Estimate the proper gain and FPS given the stellar Jmag.

    Args:
        Jmag (float): The J magnitude of the target.

    Scripts Called:

     - `kpf.guider.SetGuiderGain`
     - `kpf.guider.SetGuiderFPS`
    '''
    @classmethod
    def pre_condition(cls, args, logger, cfg):
        check_input(args, 'Jmag', allowed_types=[int, float])

    @classmethod
    def perform(cls, args, logger, cfg):
        Jmag = args.get('Jmag')
        if Jmag < 5.5:
            gain = 'low'
            fps = 100
        elif Jmag < 8.0:
            gain = 'medium'
            fps = 100
        elif Jmag < 12.0:
            gain = 'high'
            fps = 100
        elif Jmag < 12.8:
            gain = 'high'
            fps = 50
        elif Jmag < 13.8:
            gain = 'high'
            fps = 20
        elif Jmag < 14.5:
            gain = 'high'
            fps = 10
        else:
            gain = 'high'
            fps = 10
        log.info(f"Predicted GuideCamGain = {gain}")
        log.info(f"Predicted GuideFPS = {fps:d}")
        result = {'GuideCamGain': gain, 'GuideFPS': fps}
        if args.get('set', False):
            SetGuiderGain.execute(result)
            SetGuiderFPS.execute(result)
        return result

    @classmethod
    def post_condition(cls, args, logger, cfg):
        pass

    @classmethod
    def add_cmdline_args(cls, parser, cfg=None):
        parser.add_argument('Jmag', type=float,
                            help="The J magnitude of the target")
        parser.add_argument("--set", dest="set",
            default=False, action="store_true",
            help="Set these values after calculating?")
        return super().add_cmdline_args(parser, cfg)
