from kpf import log, cfg
from kpf.exceptions import *
from kpf.KPFTranslatorFunction import KPFFunction, KPFScript
from kpf.etc import ZeroPoint, EMZeroPoint, best_EMbin


class ZPETC(KPFFunction):
    '''Estimate the typical number of photons per reduced pixel near the
    specified wavelength given the Gaia G magnitude of the target and the
    exposure time.

    Args:
        Gmag (float): The Gaia G magnitude of the target.
        exptime (float): The exposure time in seconds.
        wav (str): The science wavelength (in nm) as a string. One of:
                   '452', '548', '652', '747', '852'.
        EMbin (int): The exposure meter bin (as an int). One of: 1, 2, 3, 4
    '''
    @classmethod
    def pre_condition(cls, args):
        check_input(args, 'Gmag', allowed_types=[float, int])
        check_input(args, 'exptime', allowed_types=[float, int], value_min=1)
        check_input(args, 'wav', allowed_types=[str],
                    allowed_values=list(ZeroPoint.keys()))

    @classmethod
    def perform(cls, args):
        Gmag = args.get('Gmag')
        exptime = args.get('exptime')
        wav = args.get('wav')
        photons = float(exptime*10**((Gmag - ZeroPoint[wav])/-2.5))
        if args.get('print'):
            print(f"{photons:.0f}")
        return photons

    @classmethod
    def post_condition(cls, args):
        pass

    @classmethod
    def add_cmdline_args(cls, parser):
        parser.add_argument('Gmag', type=float,
                            help="The Gaia G magnitude of the target.")
        parser.add_argument('exptime', type=float,
                            help="The exposure time in seconds.")
        parser.add_argument('wav', type=str,
                            choices=['452', '548', '652', '747', '852'],
                            help="The science wavelength (in nm) as a string.")
        parser.add_argument('--print', '-p', dest="print",
                            default=False, action="store_true",
                            help='Print the result to screen?')
        return super().add_cmdline_args(parser)


class EMADU(KPFFunction):
    '''Estimate the number of Exposure Meter ADU in the given bin corresponding
    to the specified number of science photons per reduced pixel near the
    specified wavelength

    Args:
        photons (float): The number of science photons per reduced pixel near
                         the specified wavelength.
        wav (str): The science wavelength (in nm) as a string. One of:
                   '452', '548', '652', '747', '852'.
        EMbin (int): The exposure meter bin (as an int). One of: 1, 2, 3, 4
    '''
    @classmethod
    def pre_condition(cls, args):
        check_input(args, 'photons', allowed_types=[float, int], value_min=1)
        check_input(args, 'wav', allowed_types=[str],
                    allowed_values=list(ZeroPoint.keys()))
        check_input(args, 'EMbin', allowed_types=[int],
                    allowed_values=list(EMZeroPoint.keys()))

    @classmethod
    def perform(cls, args):
        photons = args.get('photons')
        wav = args.get('wav')
        EMbin = args.get('EMbin')
        ZPdiff = ZeroPoint[wav] - EMZeroPoint[EMbin]
        ExpMeter_ADU = photons*10**(-ZPdiff/2.5)
        if args.get('print'):
            print(f"{ExpMeter_ADU:.0f}")
        return ExpMeter_ADU

    @classmethod
    def post_condition(cls, args):
        pass

    @classmethod
    def add_cmdline_args(cls, parser):
        parser.add_argument('photons', type=float,
                            help="The number of science photons per reduced pixel near the specified wavelength.")
        parser.add_argument('wav', type=str,
                            choices=['452', '548', '652', '747', '852'],
                            help="The science wavelength (in nm) as a string.")
        parser.add_argument('EMbin', type=int,
                            choices=[1, 2, 3, 4],
                            help="The exposure meter bin as an int.")
        parser.add_argument('--print', '-p', dest="print",
                            default=False, action="store_true",
                            help='Print the result to screen?')
        return super().add_cmdline_args(parser)
