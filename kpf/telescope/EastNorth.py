import ktl

from kpf import log, cfg
from kpf.exceptions import *
from kpf.KPFTranslatorFunction import KPFFunction, KPFScript
from kpf.telescope import KPF_is_selected_instrument


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
        max_offset = cfg.getfloat('telescope', 'max_offset', fallback=900)
        check_input(args, 'NodE', allowed_types=[int, float],
                    value_min=-max_offset, value_max=max_offset)
        check_input(args, 'NodN', allowed_types=[int, float],
                    value_min=-max_offset, value_max=max_offset)

    @classmethod
    def perform(cls, args):
        dcsint = cfg.getint('telescope', 'telnr', fallback=1)
        dcs = ktl.cache(f'dcs{dcsint:1d}')
        if KPF_is_selected_instrument():
            east = args.get('NodE', 0)
            north = args.get('NodN', 0)
            log.info(f'Ofsetting telescope: {east:.2f} {north:.2f}')
            dcs['RAOFF'].write(east)
            dcs['DECOFF'].write(north)
            dcs['REL2CURR'].write(True)
        else:
            INSTRUME = dcs['INSTRUME'].read()
            log.error(f'Selected instrument is {INSTRUME}, not KPF. No telescope moves allowed.')

    @classmethod
    def post_condition(cls, args):
        if KPF_is_selected_instrument():
            dcsint = cfg.getfloat('telescope', 'telnr', fallback=1)
            AXESTAT = ktl.cache(f'dcs{dcsint}', 'AXESTAT')
            tracking = AXESTAT.waitfor('=="tracking"')
            if tracking == False:
                raise FailedPostCondition('dcs.AXESTAT did not return to "tracking"', timeout=20)

    @classmethod
    def add_cmdline_args(cls, parser):
        parser.add_argument('NodE', type=float,
            help="Distance to move the telescope East in arcseconds")
        parser.add_argument('NodN', type=float,
            help="Distance to move the telescope North in arcseconds")
        return super().add_cmdline_args(parser)
