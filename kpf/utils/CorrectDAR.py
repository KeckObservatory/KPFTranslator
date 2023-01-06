import numpy as np

import ktl

from ddoitranslatormodule.KPFTranslatorFunction import KPFTranslatorFunction
from .. import (log, KPFException, FailedPreCondition, FailedPostCondition,
                FailedToReachDestination, check_input)
from .CalculateDAR import calculate_DAR_arcsec


##-------------------------------------------------------------------------
## CorrectDAR
##-------------------------------------------------------------------------
class CorrectDAR(KPFTranslatorFunction):
    '''Return the DAR correction in arcseconds between the CRED2 wavelength
    and the science wavelength.
    
    Calculation from Filippenko 1982 (PASP, 94:715-721, August 1982)
    
    ARGS:
    EL - Elevation of the telescope.
    '''
    @classmethod
    def pre_condition(cls, args, logger, cfg):
        return True

    @classmethod
    def perform(cls, args, logger, cfg):
        kpfguide = ktl.cache('kpfguide')
        dcs = ktl.cache('dcs')

        base_names = {'KPF': 'SCIENCE_BASE',
                      'SKY': 'SKY_BASE'}
        POname = dcs['PONAME'].read()
        base_name = base_names.get(POname, None)
        if base_name is None:
            log.error(f"dcs.PONAME={POname} is not recognized")
            log.error("Leaving CURRENT_BASE unmodified")
            return
#             log.error(f"Using SCIENCE_BASE for testing")
#             base_name = 'SCIENCE_BASE'

        # Calculate magnitude of DAR in arcsec
        EL = dcs['EL'].read(binary=True)*180/np.pi
        log.debug(f"Telescope elevation EL = {EL:.1f}")
        DAR_arcsec = calculate_DAR_arcsec(EL)
        log.info(f"DAR is {DAR_arcsec:.3f} arcseconds")

        # Set CURRENT_BASE
        log.info(f"dcs.PONAME is {POname}, using {base_name} as reference pixel")
        reference_pix = list(kpfguide['base_name'].read(binary=True))
        log.debug(f"Initial CURRENT_BASE = {reference_pix[0]:.1f} {reference_pix[1]:.1f}")

        va = kpfguide['VA'].read(binary=True) # in degrees
        pixel_scale = kpfguide['PSCALE'].read(binary=True) # arcsec/pix
        dx = DAR_arcsec/pixel_scale*np.sin(va*np.pi/180)
        dy = -DAR_arcsec/pixel_scale*np.cos(va*np.pi/180)
        log.info(f"Pixel shift is {dx:.1f}, {dy:.1f} = {(dx**2+dy**2)**0.5:.1f}")
        final_pixel = [reference_pix[0] + dx, reference_pix[1] + dy]
        log.debug(f"Final Pixel = {final_pix[0]:.2f} {final_pix[1]:.2f}")

        log.info(f"Writing new CURRENT_BASE = {final_pix[0]:.1f} {final_pix[1]:.1f}")
        kpfguide['CURRENT_BASE'].write(final_pix)

    @classmethod
    def post_condition(cls, args, logger, cfg):
        return True
