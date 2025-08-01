from collections import OrderedDict

import ktl

from kpf import log, cfg
from kpf.exceptions import *
from kpf.KPFTranslatorFunction import KPFFunction, KPFScript


class SetAORotator(KPFFunction):
    '''Set the AO rotator destination

    KTL Keywords Used:

    - `ao.AODCSSIM`
    - `ao.AOCOMSIM`
    - `ao.AODCSSFP`

    Args:
        dest (float): Angle in degrees for the physical drive angle of the
            rotator.
    '''
    @classmethod
    def pre_condition(cls, args):
        check_input(args, 'dest')

    @classmethod
    def perform(cls, args):
        OBRT = ktl.cache('ao', 'OBRT')
        OBRTMOVE = ktl.cache('ao', 'OBRTMOVE')
        dest = args.get('dest', 0)
        log.debug(f"Setting AO Rotator to {dest:.1f}")
        OBRT.write(dest)
        OBRTMOVE.write('1')

    @classmethod
    def post_condition(cls, args):
        OBRTSTST = ktl.cache('ao', 'OBRTSTST')
        if OBRTSTST.waitfor('== "INPOS"', timeout=180) is not True:
            raise FailedToReachDestination(OBRTSTST.read(), 'INPOS')

    @classmethod
    def add_cmdline_args(cls, parser):
        parser.add_argument('dest', type=float,
                            help="Desired rotator position")
        return super().add_cmdline_args(parser)
