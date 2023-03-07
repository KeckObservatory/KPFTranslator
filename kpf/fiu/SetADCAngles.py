import ktl
import numpy as np
from astropy.modeling import models, fitting

from ddoitranslatormodule.KPFTranslatorFunction import KPFTranslatorFunction
from .. import (log, KPFException, FailedPreCondition, FailedPostCondition,
                FailedToReachDestination, check_input)


def calculate_ADC_delta(za):
    # Zeemax model data to fit
    za_zeemax = np.array([0, 5, 10, 15, 20, 25, 30, 35, 40, 45, 50, 55, 60, 65])
    ADC_delta_zeemax = np.array([0, -2.71, -5.47, -8.32, -11.33, -14.58, -18.15, -22.19, -26.89, -32.59, -39.89, -50.15, -68.03, -90])
    poly0 = models.Polynomial1D(degree=4)
    fitter = fitting.LinearLSQFitter()
    poly = fitter(poly0, za_zeemax, ADC_delta_zeemax)
    log.debug(f"ADC Hack: poly.degree={poly.degree:d}")
    log.debug(f"ADC Hack: poly.c0={poly.c0}")
    log.debug(f"ADC Hack: poly.c1={poly.c1}")
    log.debug(f"ADC Hack: poly.c2={poly.c2}")
    log.debug(f"ADC Hack: poly.c3={poly.c3}")
    log.debug(f"ADC Hack: poly.c4={poly.c4}")
    if za >= 0 and za <= 65:
        return poly(za)
    else:
        return poly(65)


class SetADCAngles(KPFTranslatorFunction):
    '''Quick and dirty code to set ADC angles
    
    ARGS:
    =====
    None
    '''
    @classmethod
    def pre_condition(cls, args, logger, cfg):
        return True

    @classmethod
    def perform(cls, args, logger, cfg):
        kpffiu = ktl.cache('kpffiu')
        el = args.get('EL')
        za = 90 - el
        ADC_delta = calculate_ADC_delta(za)
        log.info(f"ADC Hack: za={za:.1f}, ADC_delta={ADC_delta:.1f}")

        # Constants
        common_angle = 60
        ADC1_offset = -5
        ADC2_offset = 5
        log.debug(f"ADC Hack: common_angle={common_angle:.1f}")
        log.debug(f"ADC Hack: ADC1_offset={ADC1_offset:.1f}")
        log.debug(f"ADC Hack: ADC2_offset={ADC2_offset:.1f}")

        # Calculations
        ADC1 = common_angle + ADC1_offset + za - ADC_delta
        ADC2 = common_angle + ADC2_offset - za - ADC_delta
        log.info(f"ADC Hack: Writing ADC1VAL={ADC1:.1f}, ADC2VAL={ADC2:.1f}")
        kpffiu['ADC1VAL'].write(ADC1)
        kpffiu['ADC2VAL'].write(ADC2)


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
                             'help': 'The telescope elevation to use in the calculation.'}

        parser = cls._add_args(parser, args_to_add, print_only=False)
        return super().add_cmdline_args(parser, cfg)
