import ktl

from kpf import log, cfg
from kpf.exceptions import *
from kpf.KPFTranslatorFunction import KPFFunction, KPFScript


class EastNorth(KPFFunction):
    '''Move the telescope a given distance in arcseconds East and/or North.

    Args:
        East (float): Distance to move the telescope East in arcseconds.
        North (float): Distance to move the telescope North in arcseconds.

    KTL Keywords Used:

    - `dcs.RAOFF`
    - `dcs.DECOFF`
    - `dcs.REL2CURR`
    - `dcs.AXESTAT`
    '''
    @classmethod
    def pre_condition(cls, args):
        INSTRUME = ktl.cache('dcs1', 'INSTRUME').read()
        if INSTRUME not in ['KPF', 'KPF-CC']:
            raise FaiedPreCondition(f'Selected instrument is {INSTRUME}, not KPF')
        check_input(args, 'East', allowed_types=[int, float], value_min=-600, value_max=600)
        check_input(args, 'North', allowed_types=[int, float], value_min=-600, value_max=600)

    @classmethod
    def perform(cls, args):
        dcs = ktl.cache('dcs1')
        east = args.get('East', 0)
        north = args.get('North', 0)
        dcs['RAOFF'].write(east)
        dcs['DECOFF'].write(north)
        dcs['REL2CURR'].write(True)

    @classmethod
    def post_condition(cls, args):
        AXESTAT = ktl.cache('dcs1', 'AXESTAT')
        tracking = AXESTAT.waitfor('=="tracking"')
        if tracking == False:
            raise FailedPostCondition('dcs.AXESTAT did not return to "tracking"', timeout=10)

    @classmethod
    def add_cmdline_args(cls, parser):
        parser.add_argument('East', type=float,
            help="Distance to move the telescope East in arcseconds")
        parser.add_argument('North', type=float,
            help="Distance to move the telescope North in arcseconds")
        return super().add_cmdline_args(parser)
