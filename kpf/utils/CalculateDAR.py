import numpy as np

import ktl

from kpf.KPFTranslatorFunction import KPFTranslatorFunction
from kpf import (log, KPFException, FailedPreCondition, FailedPostCondition,
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
    DARarcsec = dR(CRED2wav, za, T=T0, P=P0, f=f0, wav0=sciencewav)
    return DARarcsec


def calculate_DAR_pix(DARarcsec):
    kpfguide = ktl.cache('kpfguide')
    va = kpfguide['VA'].read(binary=True) # in degrees
    pixel_scale = kpfguide['PSCALE'].read(binary=True) # arcsec/pix
    dx = DARarcsec/pixel_scale*np.cos(va*np.pi/180)
    dy = -DARarcsec/pixel_scale*np.sin(va*np.pi/180)
    return dx, dy


##-------------------------------------------------------------------------
## CalculateDAR
##-------------------------------------------------------------------------
class CalculateDAR(KPFTranslatorFunction):
    '''Return the DAR correction in arcseconds between the CRED2 wavelength
    and the science wavelength.

    Calculation from Filippenko 1982 (PASP, 94:715-721, August 1982)

    ARGS:
    =====
    :EL: `float` Elevation of the telescope.
    '''
    @classmethod
    def pre_condition(cls, args, logger, cfg):
        pass

    @classmethod
    def perform(cls, args, logger, cfg):
        dcs = ktl.cache('dcs1')
        EL = dcs['EL'].read(binary=True)*180/np.pi
        DARarcsec = calculate_DAR_arcsec(EL)
        log.info(f"Calculated DAR for {EL:.1f} EL = {DARarcsec:.3f} arcsec")
        dx, dy = calculate_DAR_pix(DARarcsec)
        log.info(f"Pixel shift is {dx:.1f}, {dy:.1f} = {(dx**2+dy**2)**0.5:.1f}")

    @classmethod
    def post_condition(cls, args, logger, cfg):
        pass
