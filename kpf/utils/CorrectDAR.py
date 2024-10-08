import numpy as np

import ktl

from kpf.KPFTranslatorFunction import KPFTranslatorFunction
from kpf import (log, KPFException, FailedPreCondition, FailedPostCondition,
                 FailedToReachDestination, check_input)
from kpf.utils.CalculateDAR import calculate_DAR_arcsec, calculate_DAR_pix


##-------------------------------------------------------------------------
## CorrectDAR
##-------------------------------------------------------------------------
class CorrectDAR(KPFTranslatorFunction):
    '''Modify the CURRENT_BASE keyword based upon the calculated differential
    atmospheric refraction value. This is NOT the recommended method for doing
    this as it is now done automatically in the `kpfguide` keyword service. 
    This script predates full functionality of `kpfguide` and is being left in
    place only for emergency use.

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
        kpfguide = ktl.cache('kpfguide')
        dcs = ktl.cache('dcs1')
        EL = dcs['EL'].read(binary=True)*180/np.pi
        DARarcsec = calculate_DAR_arcsec(EL)
        log.info(f"DAR is {DARarcsec:.3f} arcseconds")
        dx, dy = calculate_DAR_pix(DARarcsec)
        total_pix = (dx**2+dy**2)**0.5
        log.info(f"Pixel shift is {dx:.1f}, {dy:.1f} = {total_pix:.1f}")

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

        # Set CURRENT_BASE
        log.info(f"dcs.PONAME is {POname}, using {base_name} as reference pixel")
        reference_pix = list(kpfguide[base_name].read(binary=True))
        log.debug(f"Initial CURRENT_BASE = {reference_pix[0]:.1f} {reference_pix[1]:.1f}")
        final_pixel = [reference_pix[0] + dx, reference_pix[1] + dy]
        final_pixel_string = f"{final_pixel[0]:.2f} {final_pixel[1]:.2f}"
        log.debug(f"Final Pixel = {final_pixel_string}")

        min_x_pixel = cfg.getint('guider', 'min_x_pixel', fallback=0)
        max_x_pixel = cfg.getint('guider', 'max_x_pixel', fallback=640)
        min_y_pixel = cfg.getint('guider', 'min_y_pixel', fallback=0)
        max_y_pixel = cfg.getint('guider', 'max_y_pixel', fallback=512)
        if final_pixel[0] < min_x_pixel or final_pixel[0] > max_x_pixel or\
           final_pixel[1] < min_y_pixel or final_pixel[1] > max_y_pixel:
            log.error(f"Target pixel ({final_pixel_string}) is not on guide camera")
            log.error("Leaving CURRENT_BASE unmodified")
        else:
            log.info(f"Writing new CURRENT_BASE = {final_pixel_string}")
            kpfguide['CURRENT_BASE'].write(final_pixel)

    @classmethod
    def post_condition(cls, args, logger, cfg):
        pass
