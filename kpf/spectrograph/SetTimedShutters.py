from time import sleep
import numpy as np

import ktl

from kpf import log, cfg
from kpf.exceptions import *
from kpf.KPFTranslatorFunction import KPFFunction, KPFScript


class SetTimedShutters(KPFFunction):
    '''Selects which timed shutters will be triggered by setting the
    `kpfexpose.TIMED_SHUTTERS` keyword value.
    
    ARGS:
    =====
    :TimedShutter_Scrambler: `bool` Open the TimedShutter_Scrambler shutter? (default=False)
    :TimedShutter_SimulCal: `bool` Open the TimedShutter_SimulCal shutter? (default=False)
    :TimedShutter_CaHK: `bool` Open the TimedShutter_CaHK shutter? (default=False)
    :TimedShutter_FlatField: `bool` Open the TimedShutter_FlatField shutter? (default=False)
    '''
    @classmethod
    def pre_condition(cls, args):
        pass

    @classmethod
    def perform(cls, args):
        # Scrambler 2 SimulCal 3 FF_Fiber 4 Ca_HK
        timed_shutters_list = []
        if args.get('TimedShutter_Scrambler', False) is True:
            timed_shutters_list.append('Scrambler')
        if args.get('TimedShutter_SimulCal', False) is True:
            timed_shutters_list.append('SimulCal')
        if args.get('TimedShutter_FlatField', False) is True:
            timed_shutters_list.append('FF_Fiber')
        if args.get('TimedShutter_CaHK', False) is True:
            timed_shutters_list.append('Ca_HK')
        timed_shutters_string = ','.join(timed_shutters_list)
        log.debug(f"Setting timed shutters to '{timed_shutters_string}'")
        TIMED_TARG = ktl.cache('kpfexpose', 'TIMED_TARG')
        TIMED_TARG.write(timed_shutters_string)

    @classmethod
    def post_condition(cls, args):
        TIMED_TARG = ktl.cache('kpfexpose', 'TIMED_TARG')
        TIMED_TARG.monitor()
        shutter_names = [('Scrambler', 'TimedShutter_Scrambler'),
                         ('SimulCal', 'TimedShutter_SimulCal'),
                         ('FF_Fiber', 'TimedShutter_FlatField'),
                         ('Ca_HK', 'TimedShutter_CaHK')]
        shutter_tests = [False]
        timeshim = cfg.getfloat('times', 'kpfexpose_shim_time', fallback=0.01)
        total_time = 0
        while np.all(shutter_tests) != True and total_time < 0.25:
            shutter_tests = []
            for shutter in shutter_names:
                if args.get(shutter[1], False) is True:
                    shutter_tests.append(shutter[0] in TIMED_TARG.ascii.split(','))
            sleep(timeshim)
            total_time += timeshim
        if np.all(shutter_tests) != True:
            raise FailedToReachDestination(TIMED_TARG.ascii, 'TBD')

    @classmethod
    def add_cmdline_args(cls, parser):
        parser.add_argument("--Scrambler", "--scrambler",
                            dest="TimedShutter_Scrambler",
                            default=False, action="store_true",
                            help="Open the Scrambler Timed Shutter during exposure?")
        parser.add_argument("--SimulCal", "--simulcal",
                            dest="TimedShutter_SimulCal",
                            default=False, action="store_true",
                            help="Open the SimulCal Timed Shutter during exposure?")
        parser.add_argument("--CaHK", "--HK", "--cahk", "--hk",
                            dest="TimedShutter_CaHK",
                            default=False, action="store_true",
                            help="Open the CaHK Timed Shutter during exposure?")
        parser.add_argument("--FlatField", "--flatfield",
                            dest="TimedShutter_FlatField",
                            default=False, action="store_true",
                            help="Open the FlatField Timed Shutter during exposure?")
        return super().add_cmdline_args(parser)
