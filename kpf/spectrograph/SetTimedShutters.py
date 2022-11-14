from time import sleep

import ktl

from ddoitranslatormodule.KPFTranslatorFunction import KPFTranslatorFunction
from .. import (log, KPFException, FailedPreCondition, FailedPostCondition,
                FailedToReachDestination, check_input)


class SetTimedShutters(KPFTranslatorFunction):
    '''Selects which timed shutters will be triggered by setting the
    `kpfexpose.TIMED_SHUTTERS` keyword value.
    
    ARGS:
    TimedShutter_Scrambler (bool) - Open the TimedShutter_Scrambler shutter? (default=False)
    TimedShutter_SimulCal (bool) - Open the TimedShutter_SimulCal shutter? (default=False)
    TimedShutter_CaHK (bool) - Open the TimedShutter_CaHK shutter? (default=False)
    TimedShutter_FlatField (bool) - Open the TimedShutter_FlatField shutter? (default=False)
    '''
    @classmethod
    def pre_condition(cls, args, logger, cfg):
        return True

    @classmethod
    def perform(cls, args, logger, cfg):
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
        log.debug(f"  Setting timed shutters to '{timed_shutters_string}'")
        kpfexpose = ktl.cache('kpfexpose')
        kpfexpose['TIMED_TARG'].write(timed_shutters_string)

    @classmethod
    def post_condition(cls, args, logger, cfg):
        kpfexpose = ktl.cache('kpfexpose')
        timeshim = cfg.get('times', 'kpfexpose_shim_time', fallback=0.01)
        sleep(timeshim)
        shutters = kpfexpose['TIMED_TARG'].read()
        log.debug(f"TIMED_TARG: {shutters}")
        shutter_list = shutters.split(',')
        shutter_names = [('Scrambler', 'TimedShutter_Scrambler'),
                         ('SimulCal', 'TimedShutter_SimulCal'),
                         ('FF_Fiber', 'TimedShutter_FlatField'),
                         ('Ca_HK', 'TimedShutter_CaHK')]
        for shutter in shutter_names:
            shutter_status = shutter[0] in shutter_list
            shutter_target = args.get(shutter[1], False)
            if shutter_target != shutter_status:
                raise FailedToReachDestination(shutter_status, shutter_target)

    @classmethod
    def add_cmdline_args(cls, parser, cfg=None):
        '''The arguments to add to the command line interface.
        '''
        parser = cls._add_bool_arg(parser, 'TimedShutter_Scrambler',
                                   'Open the TimedShutter_Scrambler shutter?',
                                   default=False)
        parser = cls._add_bool_arg(parser, 'TimedShutter_SimulCal',
                                   'Open the TimedShutter_SimulCal shutter?',
                                   default=False)
        parser = cls._add_bool_arg(parser, 'TimedShutter_CaHK',
                                   'Open the TimedShutter_CaHK shutter?',
                                   default=False)
        parser = cls._add_bool_arg(parser, 'TimedShutter_FlatField',
                                   'Open the TimedShutter_FlatField shutter?',
                                    default=False)
        return super().add_cmdline_args(parser, cfg)
