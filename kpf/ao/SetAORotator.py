from collections import OrderedDict

import ktl

from kpf.KPFTranslatorFunction import KPFTranslatorFunction
from kpf import (log, KPFException, FailedPreCondition, FailedPostCondition,
                 FailedToReachDestination, check_input)


class SetAORotator(KPFTranslatorFunction):
    '''# Description
    Set the AO rotator destination

    ## KTL Keywords Used
    - `ao.AODCSSIM`
    - `ao.AOCOMSIM`
    - `ao.AODCSSFP`

    ## Scripts Called

    None

    ## Parameters

    **dest** (`float`)
    > Angle in degrees for the physical drive angle of the rotator.
    '''
    @classmethod
    def pre_condition(cls, args, logger, cfg):
        check_input(args, 'dest')

    @classmethod
    def perform(cls, args, logger, cfg):
        ao = ktl.cache('ao')
        dest = args.get('dest', 0)
        log.debug(f"Setting AO Rotator to {dest:.1f}")
        ao['OBRT'].write(dest)
        ao['OBRTMOVE'].write('1')

    @classmethod
    def post_condition(cls, args, logger, cfg):
        success = ktl.waitfor('($ao.OBRTSTST == INPOS)', timeout=180)
        if success is not True:
            ao = ktl.cache('ao')
            raise FailedToReachDestination(ao['OBRTSTST'].read(), 'INPOS')

    @classmethod
    def add_cmdline_args(cls, parser, cfg=None):
        parser.add_argument('dest', type=float,
                            help="Desired rotator position")
        return super().add_cmdline_args(parser, cfg)
