from kpf.KPFTranslatorFunction import KPFTranslatorFunction
from kpf import (log, KPFException, FailedPreCondition, FailedPostCondition,
                 FailedToReachDestination, check_input)
from kpf.fvc.SetFVCExpTime import SetFVCExpTime


class PredictFVCParameters(KPFTranslatorFunction):
    '''Estimate the exposure time given the stellar Jmag and which camera.

    Based on scaling from a single, poorly measured data point:
    For Vmag ~ 4, the SCIFVC_exptime = 1 and CAHKFVC_exptime = 15

    Args:
    =====
    :Gmag: The G magnitude of the target
    '''
    @classmethod
    def pre_condition(cls, args, logger, cfg):
        check_input(args, 'Gmag', allowed_types=[int, float])

    @classmethod
    def perform(cls, args, logger, cfg):
        Gmag = args.get('Gmag')
        camera = args.get('camera')
        delta_mag = 4 - Gmag
        flux_ratio = 10**(delta_mag/2.5)
        if flux_ratio > 10:
            exptime = {'SCI': 0.1,
                       'CAHK': 1.5}
        elif flux_ratio > 5:
            exptime = {'SCI': 0.2,
                       'CAHK': 3}
        elif flux_ratio > 2:
            exptime = {'SCI': 0.5,
                       'CAHK': 8}
        elif flux_ratio > 0.5:
            exptime = {'SCI': 1,
                       'CAHK': 15}
        elif flux_ratio > 0.2:
            exptime = {'SCI': 5,
                       'CAHK': 15}
        elif flux_ratio > 0.05:
            exptime = {'SCI': 10,
                       'CAHK': 15}
        result = {'camera': camera, 'exptime': exptime[camera]}
        print(result)
        if args.get('set', False):
            SetFVCExpTime.execute(result)
        return result

    @classmethod
    def post_condition(cls, args, logger, cfg):
        pass

    @classmethod
    def add_cmdline_args(cls, parser, cfg=None):
        parser.add_argument('camera', type=str,
                            help='The FVC camera (SCI, CAHK)')
        parser.add_argument('Gmag', type=float,
                            help="The G magnitude of the target")
        parser.add_argument("--set", dest="set",
            default=False, action="store_true",
            help="Set these values after calculating?")
        return super().add_cmdline_args(parser, cfg)
