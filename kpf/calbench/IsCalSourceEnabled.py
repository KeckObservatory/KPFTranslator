import ktl

from kpf import log, cfg
from kpf.exceptions import *
from kpf.KPFTranslatorFunction import KPFFunction, KPFScript
from kpf.calbench import standardize_lamp_name


class IsCalSourceEnabled(KPFFunction):
    '''Return a boolean indicating whether the input CalSource is enabled as
    reported by the kpfconfig.%_ENABLED keywords.

    Args:
        CalSource (str): Which lamp to check? Allowed Values: EtalonFiber,
            BrdbandFiber, U_gold, U_daily, Th_daily, Th_gold, SoCal-CalFib,
            LFCFiber, SoCal-SciSky, WideFlat

    Returns:
        The return value. True for enabled, False for disabled.

    KTL Keywords Used:

    - `kpfcal.OCTAGON`
    - `kpfconfig.BRDBANDFIBER_ENABLED`
    - `kpfconfig.U_GOLD_ENABLED`
    - `kpfconfig.U_DAILY_ENABLED`
    - `kpfconfig.TH_DAILY_ENABLED`
    - `kpfconfig.TH_GOLD_ENABLED`
    - `kpfconfig.FF_FIBER_ENABLED`
    - `kpfconfig.EXPMLED_ENABLED`
    - `kpfconfig.HKLED_ENABLED`
    - `kpfconfig.SCILED_ENABLED`
    - `kpfconfig.SKYLED_ENABLED`
    '''
    @classmethod
    def pre_condition(cls, args):
        keyword = ktl.cache('kpfcal', 'OCTAGON')
        allowed_values = list(keyword._getEnumerators())
        if 'Unknown' in allowed_values:
            allowed_values.pop(allowed_values.index('Unknown'))
        allowed_values.append('SoCal-SciSky')
        allowed_values.append('WideFlat')
        check_input(args, 'CalSource', allowed_values=allowed_values)

    @classmethod
    def perform(cls, args):
        calsource = args.get('CalSource')
        if calsource in ['BrdbandFiber', 'WideFlat', 'Th_daily', 'Th_gold', 'U_daily', 'U_gold']:
            lamp_name = standardize_lamp_name(calsource)
        elif calsource in ['LFCFiber', 'EtalonFiber']:
            lamp_name = calsource.upper()
        elif calsource in ['SoCal-CalFib', 'SoCal-SciSky']:
            lamp_name = calsource.replace('-', '_').replace('Sky', 'FIB')
        else:
            log.warning(f"IsCalSourceEnabled does not recognize '{calsource}'")
            return True
        lamp_enabledkw = ktl.cache('kpfconfig', f'{lamp_name}_ENABLED')
        lamp_enabled = lamp_enabledkw.read(binary=True)
        if lamp_enabled is True:
            log.debug(f"Cal source {calsource} is enabled")
            print(f"Cal source {calsource} is enabled")
        else:
            log.warning(f"Cal source {calsource} is disabled")
        return lamp_enabled

    @classmethod
    def post_condition(cls, args):
        pass

    @classmethod
    def add_cmdline_args(cls, parser):
        parser.add_argument('CalSource', type=str,
                            choices=['BrdbandFiber', 'WideFlat', 'Th_daily',
                                     'Th_gold', 'U_daily', 'U_gold',
                                     'LFCFiber', 'EtalonFiber', 
                                     'SoCal-CalFib', 'SoCal-SciSky'],
                            help='Which lamp to check?')
        return super().add_cmdline_args(parser)
