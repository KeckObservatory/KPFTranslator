import time
import ktl

from kpf.KPFTranslatorFunction import KPFTranslatorFunction
from kpf import (log, KPFException, FailedPreCondition, FailedPostCondition,
                 FailedToReachDestination, check_input)


def expeter_flux_target(spectrograph_flux, band):
    slope = {1:  4.569,
             2: 11.125,
             3: 10.026,
             4: 12.446}[band]
    expmeter_flux = slope*spectrograph_flux
    return expmeter_flux


class SetExpMeterTerminationParameters(KPFTranslatorFunction):
    '''Sets the exposure meter exposure termination control parameters
    
    Threshold bin definition (from kpf_expmeter.THRESHOLDBIN)
    Values: 0 All 1 498.125 2 604.375 3 710.625 4 816.875
    
    Relationship (slope) between expmeter flux and science spectrograph flux
    (from Jon Zink: https://cal-planet-search.slack.com/archives/CE57W8VL0/p1692294839416559?thread_ts=1692226289.791179&cid=CE57W8VL0)
    bin,m
    498.12,4.568570548557381
    604.38,11.125201914680732
    710.62,10.02578758982348
    816.88,12.446153099971543
    
    Args:
    =====
    :Band: Which of the 4 exposure meter bands to use (1=498nm, 2=604nm, 3=711nm, 4=817nm)
    :Flux: The flux (e/nm) in the science spectrum desired
    '''
    @classmethod
    def pre_condition(cls, args, logger, cfg):
        check_input(args, 'ExpMeterThreshold', allowed_types=[int, float],
                    value_min=0)
        check_input(args, 'ExpMeterBin', allowed_types=[int],
                    allowed_values=[1,2,3,4])

    @classmethod
    def perform(cls, args, logger, cfg):
        spectrograph_flux = args.get('ExpMeterThreshold')
        band = args.get('ExpMeterBin')
        expmeter_flux = expeter_flux_target(spectrograph_flux, band)

        kpf_expmeter = ktl.cache('kpf_expmeter')
        kpf_expmeter['THRESHOLDBIN'].write(band)
        kpf_expmeter['THRESHOLD'].write(expmeter_flux)
        kpf_expmeter['USETHRESHOLD'].write('Yes')

    @classmethod
    def post_condition(cls, args, logger, cfg):

    @classmethod
    def add_cmdline_args(cls, parser, cfg=None):
        '''The arguments to add to the command line interface.
        '''
        parser.add_argument('ExpMeterBin', type=int,
                            choices=[1,2,3,4],
                            help="Which exposure meter band to use (1, 2, 3, or 4)")
        parser.add_argument('ExpMeterThreshold', type=float,
                            help="Threshold flux in e-/nm in the main spectrograph",
        return super().add_cmdline_args(parser, cfg)
