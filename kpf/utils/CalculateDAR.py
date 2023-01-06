import numpy as np

import ktl
from astropy import wcs

from ddoitranslatormodule.KPFTranslatorFunction import KPFTranslatorFunction
from .. import (log, KPFException, FailedPreCondition, FailedPostCondition,
                FailedToReachDestination, check_input)


##-------------------------------------------------------------------------
## Utility functions
## from Filippenko 1982 (PASP, 94:715-721, August 1982)
##-------------------------------------------------------------------------
def n_15760(wav):
    '''wav in microns'''
    foo = 64.328 + 29498.1/(146-(1/wav)**2) + 255.4/(41-(1/wav)**2)
    n_15760 = foo/10**6 + 1
    return n_15760

def n(wav, T=7, P=600, f=8):
    '''T air temperature in deg C
    P air pressure in mm Hg
    f is water vapor pressure in mm Hg
    '''
    n0 = (n_15760(wav) - 1) * P*(1+(1.049 - 0.0157*T)*10**-6*P) / (720.883*(1+0.003661*T)) + 1
    reduction = (0.0624 - 0.000680/wav**2)/(1+0.003661*T)*f
    n = ( (n0-1)*10**6 - reduction ) / 10**6 + 1
    return n

def dR(wav, z, T=7, P=600, f=8, wav0=0.5):
    '''z is zenith angle in degrees
    '''
    z *= np.pi/180 # convert to radians
    dR = 206265 * ( n(wav, T=T, P=P, f=f) - n(wav0, T=T, P=P, f=f) ) * np.tan(z)
    return dR


def calculate_DAR_arcsec(EL):
    # Maunakea atmospheric values
    za = 90-EL
    args = {} # Fix later
    T0 = args.get('T0', 0)
    P0 = args.get('P0', 465)
    f0 = args.get('f0', 4.5)
    CRED2wav = args.get('CRED2wav', 1.075)
    sciencewav = args.get('sciencewav', 0.55)
    DAR_arcsec = dR(CRED2wav, za, T=T0, P=P0, f=f0, wav0=sciencewav)
    log.info(f"Calculated DAR for {EL:.1f} EL = {DAR_arcsec:.3f} arcsec")
    return DAR_arcsec


##-------------------------------------------------------------------------
## CalculateDAR
##-------------------------------------------------------------------------
class CalculateDAR(KPFTranslatorFunction):
    '''Return the DAR correction in arcseconds between the CRED2 wavelength
    and the science wavelength.
    
    Calculation from Filippenko 1982 (PASP, 94:715-721, August 1982)
    
    ARGS:
    EL - Elevation of the telescope.
    '''
    @classmethod
    def pre_condition(cls, args, logger, cfg):
        check_input(args, 'EL', value_min=1, value_max=90)
        return True

    @classmethod
    def perform(cls, args, logger, cfg):
        EL = float(args.get('EL'))
        DARarcsec = calculate_DAR_arcsec(EL)
        print(f"DAR in arcsec = {DARarcsec:.3f}")

    @classmethod
    def post_condition(cls, args, logger, cfg):
        return True

    @classmethod
    def add_cmdline_args(cls, parser, cfg=None):
        '''The arguments to add to the command line interface.
        '''
        from collections import OrderedDict
        args_to_add = OrderedDict()
        args_to_add['EL'] = {'type': float,
                    'help': 'Elevation in degrees (90-ZA)'}
        parser = cls._add_args(parser, args_to_add, print_only=False)
        return super().add_cmdline_args(parser, cfg)
