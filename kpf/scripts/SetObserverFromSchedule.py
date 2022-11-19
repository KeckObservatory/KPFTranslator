from datetime import datetime, timedelta

import ktl

from ddoitranslatormodule.KPFTranslatorFunction import KPFTranslatorFunction
from .. import (log, KPFException, FailedPreCondition, FailedPostCondition,
                FailedToReachDestination, check_input)
from ..spectrograph.SetObserver import SetObserver
from . import get_schedule


class SetObserverFromSchedule(KPFTranslatorFunction):
    '''
    '''
    @classmethod
    def pre_condition(cls, args, logger, cfg):
        check_input(args, 'progname')
        return True

    @classmethod
    def perform(cls, args, logger, cfg):
        utnow = datetime.utcnow()
        date = utnow-timedelta(days=1)
        date_str = date.strftime('%Y-%m-%d')
        KPF_programs = [s for s in get_schedule(date_str, 1)
                        if s['Instrument'] == 'KPF']
        log.debug(f"Found {len(KPF_programs)} KPF programs in schedule for tonight")

        progname = args.get('progname')
        this_program = [p for p in KPF_programs if p['ProjCode'] == progname]
        log.debug(f"Found {len(this_program)} entries for {progname} in schedule for tonight")
        
        if len(this_program) > 0:
            observers = this_program[0]['Observers']
            log.info(f"Setting observer list based on telescope schedule:")
            log.info(f"{observers}")
            SetObserver.execute({'observer': observers})
        else:
            log.error(f"Failed to set observers. Could not find this program on the schedule.")

    @classmethod
    def post_condition(cls, args, logger, cfg):
        pass
#         observer = args.get('observer')
#         timeout = cfg.get('times', 'kpfexpose_timeout', fallback=0.01)
#         expr = f"($kpfexpose.OBSERVER == '{observer}')"
#         success = ktl.waitFor(expr, timeout=timeout)
#         if success is not True:
#             observerkw = ktl.cache('kpfexpose', 'OBSERVER')
#             raise FailedToReachDestination(observerkw.read(), observer)

    @classmethod
    def add_cmdline_args(cls, parser, cfg=None):
        '''The arguments to add to the command line interface.
        '''
        from collections import OrderedDict
        args_to_add = OrderedDict()
        args_to_add['progname'] = {'type': str,
                                   'help': 'The PROGNAME keyword.'}
        parser = cls._add_args(parser, args_to_add, print_only=False)
        return super().add_cmdline_args(parser, cfg)
