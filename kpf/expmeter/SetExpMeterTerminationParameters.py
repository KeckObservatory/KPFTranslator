import time
import numpy as np
import ktl

from kpf import log, cfg
from kpf.exceptions import *
from kpf.KPFTranslatorFunction import KPFFunction, KPFScript


def expeter_flux_target(Mphotons_per_A, band):
    # photons/A near bin center divided by TOTCORR
    # bin1 / 498.125nm = 0.104 (1.4%)
    # bin2 / 604.375nm = 0.116 (0.8%)
    # bin3 / 710.625nm = 0.087 (2.2%)
    # bin4 / 816.875nm = 0.116 (0.8%)
    peak_photon_ratios = {'498.125': 0.104,
                          '604.375': 0.116,
                          '710.625': 0.087,
                          '816.875': 0.116}
    expmeter_threshold = 1e6*Mphotons_per_A/peak_photon_ratios[band]
    # Estimate SNR using empirical relation from example observations.
    # SNR is taken from DRP output at a few wavelengths.
    snr_estimate = 120*(Mphotons_per_A)**0.5
    return expmeter_threshold, snr_estimate


class SetExpMeterTerminationParameters(KPFFunction):
    '''Sets the exposure meter exposure termination control parameters

    Args:
        Band (int): Which of the 4 exposure meter bands to use? 0=All, 1=498nm,
            2=604nm, 3=711nm, 4=817nm (from kpf_expmeter.THRESHOLDBIN).
        Flux (float): The target flux (e/nm) in the science spectrum.

    KTL Keywords Used:

    - `kpf_expmeter.THRESHOLDBIN`
    - `kpf_expmeter.THRESHOLD`
    - `kpf_expmeter.USETHRESHOLD`
    '''
    @classmethod
    def pre_condition(cls, args):
        check_input(args, 'ExpMeterThreshold', allowed_types=[int, float],
                    value_min=0)
#         check_input(args, 'ExpMeterBin', allowed_types=[int, float, str])
#         band = float(args.get('ExpMeterBin'))
#         tbin = ktl.cache('kpf_expmeter', 'THRESHOLDBIN')
#         allowed_values = list(tbin._getEnumerators())
#         allowed_values.pop(allowed_values.index('All'))
#         allowed_floats = np.array([float(x) for x in allowed_values])
#         if int(band) not in [1, 2, 3, 4]:
#             band = (np.abs(allowed_floats-band)).argmin()+1
#         if band not in [1, 2, 3, 4]:
#             raise FailedPreCondition(f'Unable to parse ExpMeterBin: {args.get("ExpMeterBin")}')

    @classmethod
    def perform(cls, args):
        tbin = ktl.cache('kpf_expmeter', 'THRESHOLDBIN')
        allowed_values = list(tbin._getEnumerators())
        allowed_values.pop(allowed_values.index('All'))
        allowed_floats = np.array([float(x) for x in allowed_values])

        floatband = float(args.get('ExpMeterBin'))
        if int(floatband) in [1, 2, 3, 4]:
            intband = int(floatband)
        else:
            intband = (np.abs(allowed_floats-floatband)).argmin()+1
        stringband = {1: '498.125', 2: '604.375', 3: '710.625', 4: '816.875'}[intband]

        spectrograph_flux = args.get('ExpMeterThreshold')
        expmeter_flux, snr_estimate = expeter_flux_target(spectrograph_flux, stringband)
        kpf_expmeter = ktl.cache('kpf_expmeter')
        kpf_expmeter['THRESHOLDBIN'].write(stringband)
        kpf_expmeter['THRESHOLD'].write(expmeter_flux)
        kpf_expmeter['USETHRESHOLD'].write('Yes')

    @classmethod
    def post_condition(cls, args):
        pass

    @classmethod
    def add_cmdline_args(cls, parser):
        parser.add_argument('ExpMeterBin', type=str,
                            choices=['1', '2', '3', '4', '498.125','604.375','710.625','816.875'],
                            help="Which exposure meter band to use")
        parser.add_argument('ExpMeterThreshold', type=float,
                            help="Threshold flux in Mphotons/A in the main spectrograph")
        return super().add_cmdline_args(parser)
