import numpy as np

import ktl
from astropy import wcs

from ddoitranslatormodule.KPFTranslatorFunction import KPFTranslatorFunction
from .. import (log, KPFException, FailedPreCondition, FailedPostCondition,
                FailedToReachDestination, check_input)
from .CalculateDAR import calculate_DAR_arcsec


def calculate_DAR_pix(EL):
    DAR_arcsec = calculate_DAR_arcsec(EL)

    kpfguide = ktl.cache('kpfguide')
    w = wcs.WCS(naxis=2)
    w.wcs.crpix = [kpfguide['CRPIX1Y'].read(binary=True),
                   kpfguide['CRPIX2Y'].read(binary=True)]
    w.wcs.crval = [kpfguide['CRVAL1Y'].read(binary=True),
                   kpfguide['CRVAL2Y'].read(binary=True)]
    w.wcs.ctype = ["RA---TAN", "DEC--TAN"]
    w.wcs.pc = np.array([[kpfguide['CD1_1Y'].read(binary=True), 
                          kpfguide['CD1_2Y'].read(binary=True)],
                         [kpfguide['CD2_1Y'].read(binary=True),
                          kpfguide['CD2_2Y'].read(binary=True)]])

    reference_pix = list(kpfguide['CURRENT_BASE'].read(binary=True))
    log.info(f"Initial CURRENT_BASE = {reference_pix[0]:.2f} {reference_pix[1]:.2f}")
    azel = w.all_pix2world(np.array([reference_pix], dtype=np.float), 0)[0]
    log.debug(f"Initial Az, EL = {azel}")
    modified_azel = np.array([[azel[0],azel[1] + DAR_arcsec/60/60]], dtype=np.float)
    log.debug(f"Modified Az, EL = {modified_azel[0]}")
    final_pix = w.all_world2pix(modified_azel, 0)[0]
    
    delta_pix = ((final_pix[0]-reference_pix[0])**2 + (final_pix[1]-reference_pix[1])**2)**0.5
    log.info(f"Pixel shift is {delta_pix:.1f}")
    
    return final_pix


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
        base_names = {'KPF': 'SCIENCE_BASE',
                      'SKY': 'SKY_BASE'}
        POname = ktl.cache('dcs', 'PONAME').read()
        base_name = base_names.get(POname, None)
        if base_name is None:
            log.error(f"dcs.PONAME={POname} is not recognized")
            return

        # Set CURRENT_BASE
        log.info(f"dcs.PONAME is {POname}, setting CURRENT_BASE to {base_name}")
        reference_pix = list(kpfguide[base_name].read(binary=True))
        kpfguide['CURRENT_BASE'].write(reference_pix)

        EL = ktl.cache('dcs', 'EL').read(binary=True)
        final_pix = calculate_DAR_pix(EL)
        log.info(f"Writing new CURRENT_BASE = {final_pix[0]:.2f} {final_pix[1]:.2f}")
        kpfguide['CURRENT_BASE'].write(final_pix)

    @classmethod
    def post_condition(cls, args, logger, cfg):
        return True
