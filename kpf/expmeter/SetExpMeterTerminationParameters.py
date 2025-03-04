import time
import ktl

from kpf import log, cfg
from kpf.exceptions import *
from kpf.KPFTranslatorFunction import KPFFunction, KPFScript


def expeter_flux_target(spectrograph_flux, band):
    slope = {'498.125': 7503.438,
             '604.375': 50044.28,
             '710.625': 30752.42,
             '816.875': 42361.16}
    expmeter_flux = spectrograph_flux*slope[band]
    return expmeter_flux


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
        check_input(args, 'ExpMeterBin', allowed_types=[int, float, str])
        band = float(args.get('ExpMeterBin'))
        tbin = ktl.cache('kpf_expmeter', 'THRESHOLDBIN')
        allowed_values = list(tbin._getEnumerators())
        allowed_values.pop(allowed_values.index('All'))
        allowed_floats = np.array([float(x) for x in allowed_values])
        if int(band) not in [1, 2, 3, 4]:
            band = (np.abs(allowed_floats-band)).argmin()+1
        if band not in [1, 2, 3, 4]:
            raise FailedPreCondition(f'Unable to parse ExpMeterBin: {args.get("ExpMeterBin")}')

    @classmethod
    def perform(cls, args):
        band = float(args.get('ExpMeterBin'))
        tbin = ktl.cache('kpf_expmeter', 'THRESHOLDBIN')
        allowed_values = list(tbin._getEnumerators())
        allowed_values.pop(allowed_values.index('All'))
        allowed_floats = np.array([float(x) for x in allowed_values])
        if int(band) not in [1, 2, 3, 4]:
            band = (np.abs(allowed_floats-band)).argmin()+1

        spectrograph_flux = args.get('ExpMeterThreshold')
        expmeter_flux = expeter_flux_target(spectrograph_flux, band)
        kpf_expmeter = ktl.cache('kpf_expmeter')
        kpf_expmeter['THRESHOLDBIN'].write(band)
        kpf_expmeter['THRESHOLD'].write(expmeter_flux)
        kpf_expmeter['USETHRESHOLD'].write('Yes')

    @classmethod
    def post_condition(cls, args):
        pass

    @classmethod
    def add_cmdline_args(cls, parser):
        parser.add_argument('ExpMeterBin', type=int,
                            choices=[1,2,3,4],
                            help="Which exposure meter band to use (1, 2, 3, or 4)")
        parser.add_argument('ExpMeterThreshold', type=float,
                            help="Threshold flux in e-/nm in the main spectrograph")
        return super().add_cmdline_args(parser)
