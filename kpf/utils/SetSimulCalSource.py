from pathlib import Path

import ktl

from kpf.KPFTranslatorFunction import KPFTranslatorFunction
from kpf import (log, KPFException, FailedPreCondition, FailedPostCondition,
                 FailedToReachDestination, check_input)


##-------------------------------------------------------------------------
## SetSimulCalSource
##-------------------------------------------------------------------------
class SetSimulCalSource(KPFTranslatorFunction):
    '''Set the slew cal and simultaneous calibration source.

    Valid names: EtalonFiber, U_gold, U_daily, Th_daily, Th_gold, LFCFiber

    ARGS:
    =====
    :calsource: The calibration source to use (must be one of Etalon, LFC,
                Th_daily, Th_gold, U_daily, U_gold).

    '''
    @classmethod
    def pre_condition(cls, args, logger, cfg):
        valid_names = ['EtalonFiber', 'U_gold', 'U_daily', 'Th_daily',
                       'Th_gold', 'LFCFiber']
        if args.get('calsource', None) not in valid_names:
            raise FailedPreCondition(f"calsource '{calsource}' must be one of {valid_names}")

    @classmethod
    def perform(cls, args, logger, cfg):
        log.info(f"Setting simul cal / slew cal source")
        calsource = args.get('calsource')
        kpfconfig = ktl.cache('kpfconfig')
        slew_cal_file = Path(f'/kroot/rel/default/data/obs/kpf/SlewCal_{calsource}.yaml')
        if slew_cal_file.exists() is False:
            raise KPFException(f'The slew cal file for {calsource} does not exist')
        else:
            log.info(f'Writing kpfconfig.SIMULCALSOURCE = {calsource}')
            kpfconfig['SIMULCALSOURCE'].write(calsource)
            log.info(f'Writing kpfconfig.SLEWCALFILE = {slew_cal_file}')
            kpfconfig['SLEWCALFILE'].write(f"{slew_cal_file}")

    @classmethod
    def post_condition(cls, args, logger, cfg):
        pass

    @classmethod
    def add_cmdline_args(cls, parser, cfg=None):
        '''The arguments to add to the command line interface.
        '''
        from collections import OrderedDict
        args_to_add = OrderedDict()
        args_to_add['calsource'] = {'type': str,
                                    'help': 'Which lamp to use for simultaneous calibration and slew cals.'}

        parser = cls._add_args(parser, args_to_add, print_only=False)
        return super().add_cmdline_args(parser, cfg)
