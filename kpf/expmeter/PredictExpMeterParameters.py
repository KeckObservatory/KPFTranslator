from kpf.KPFTranslatorFunction import KPFTranslatorFunction
from kpf import (log, KPFException, FailedPreCondition, FailedPostCondition,
                 FailedToReachDestination, check_input)

# Excel Table exported to CSV:
#
# Gmag (mag),Exp (s),ADU / spectral bin,SNR / spectral bin,ADU total,SNR total,Exp (s) (5 mag ext.),SNR/bin (5 mag ext.),SNR total (5 mag ext.),notes
# 3.3,0.5,12000000,3464,180000000,13416,0.5,346,1342,Tau Ceti (Teff=5200 K); 50% of saturation - use for scaling
# 4,0.5,6297690,2510,94465343,9719,1,502,1944,
# 5,1,5014311,2239,75214661,8673,2,633,2453,
# 6,1,1996233,1413,29943496,5472,2,400,1548,
# 7,1,794715,891,11920720,3453,4,504,1953,
# 8,1,316382,562,4745724,2178,4,318,1232,
# 9,2,251908,502,3778614,1944,8,402,1555,
# 10,2,100286,317,1504293,1226,16,507,1962,
# 11,4,79849,283,1197740,1094,16,320,1238,switch to white light for midpoint in 5 mag extinction case
# 12,4,31789,178,476829,691,16,202,781,
# 13,8,25311,159,379658,616,16,127,493,
# 14,8,10076,100,151145,389,16,80,311,switch to white light for midpoint in no extinction case
# 15,16,8023,90,120343,347,16,51,196,
# 16,16,3194,57,47910,219,16,32,124,
# ,,,,,,,Don’t observe,,
# ,,,,,,,,,
# ,,"Scaled off of Tau Ceti observation (KP.20230114.24430.58. frameno=24450) which had 30,000 ADU (peak) in raw EM pixels",,,,,,,
# ,,Two cases considered: no extinction and 5 mag of extinction,,,,,,,
# ,,"For bright stars, avoid saturation by using short Texp (=0.5 sec).  These stars have enough SNR so that chromatic T_mid can be computed.",,,,,,,
# ,,"For the faintest stars, use longest Texp (=16 sec) that gives reasonable T_mid based on Jon Zink's simulation.",,,,,,,
# ,,"In good conditions, there is a magnitude where there is insufficient flux per spectral bin and T_mid from white light is more reliable",,,,,,,
# ,,"In poor conditions, this magnitude is a smaller number",,,,,,,
# ,,,,,,,,,
# ,,Notes:,,,,,,,
# ,,ADU/spectral bin is really rough (a couple factors of two) and is based on flux estimates from counting ADU in DS9,,,,,,,
# ,,We haven't accounted for gain in the above analysis (ADU -> e-),,,,,,,


class PredictExpMeterParameters(KPFTranslatorFunction):
    '''Estimate the proper exposure meter exposure time given the stellar Gmag.
    
    Args:
    =====
    :Gmag: The Gaia g magnitude of the target
    '''
    @classmethod
    def pre_condition(cls, args, logger, cfg):
        check_input(args, 'Gmag', allowed_types=[int, float])

    @classmethod
    def perform(cls, args, logger, cfg):
        Gmag = args.get('Gmag')
        if Gmag < 4.0:
            exptime = 0.5
        elif Gmag < 9.0:
            exptime = 1.0
        elif Gmag < 11.0:
            exptime = 2.0
        elif Gmag < 13.0:
            exptime = 4.0
        elif Gmag < 15.0:
            exptime = 8.0
        else:
            exptime = 16.0
        log.info(f"Predicted ExpMeterExpTime = {exptime:.1f} s")
        return {'ExpMeterExpTime': exptime}

    @classmethod
    def post_condition(cls, args, logger, cfg):
        pass

    @classmethod
    def add_cmdline_args(cls, parser, cfg=None):
        parser.add_argument('Gmag', type=float,
                            help="The Gaia g magnitude of the target")
        return super().add_cmdline_args(parser, cfg)

