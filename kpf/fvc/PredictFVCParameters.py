from kpf import log, cfg, check_input
from kpf.exceptions import *
from kpf.KPFTranslatorFunction import KPFFunction, KPFScript
from kpf.fvc.SetFVCExpTime import SetFVCExpTime


class PredictFVCParameters(KPFFunction):
    '''Estimate the exposure time given the stellar Jmag and which camera.

    Based on scaling from a single, poorly measured data point:
    For Vmag ~ 4, the SCIFVC_exptime = 1 and CAHKFVC_exptime = 15

    Args:
        Gmag (float): The G magnitude of the target.
    '''
    @classmethod
    def pre_condition(cls, args):
        check_input(args, 'Gmag', allowed_types=[int, float])

    @classmethod
    def perform(cls, args):
        Gmag = args.get('Gmag')
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
        result = {'SCIFVC_exptime': exptime['SCI'],
                  'CAHKFVC_exptime': exptime['CAHK']}
        print(result)
        if args.get('set', False):
            SetFVCExpTime.execute({'camera': 'SCI', 'exptime': exptime['SCI']})
            SetFVCExpTime.execute({'camera': 'CAHK', 'exptime': exptime['CAHK']})
        return result

    @classmethod
    def post_condition(cls, args):
        pass

    @classmethod
    def add_cmdline_args(cls, parser, cfg=None):
        parser.add_argument('Gmag', type=float,
                            help="The G magnitude of the target")
        parser.add_argument("--set", dest="set",
            default=False, action="store_true",
            help="Set these values after calculating?")
        return super().add_cmdline_args(parser, cfg)
