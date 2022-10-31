

import ktl

from ddoitranslatormodule.KPFTranslatorFunction import KPFTranslatorFunction


class SetTimedShutters(KPFTranslatorFunction):
    '''Selects which timed shutters will be triggered by setting the
    `kpfexpose.TIMED_SHUTTERS` keyword value.
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
        print(f"  Setting timed shutters to '{timed_shutters_string}'")
        kpfexpose = ktl.cache('kpfexpose')
        kpfexpose['TIMED_SHUTTERS'].write(timed_shutters_string)

    @classmethod
    def post_condition(cls, args, logger, cfg):
        kpfexpose = ktl.cache('kpfexpose')
        shutters = kpfexpose['TIMED_SHUTTERS'].read()
        shutter_list = shutters.split(',')

        Scrambler_shutter_status = 'Scrambler' in shutter_list
        Scrambler_shutter_target = args.get('TimedShutter_Scrambler', False)
        if Scrambler_shutter_target != Scrambler_shutter_status:
            msg = (f"Final Scrambler timed shutter mismatch: "
                   f"{Scrambler_shutter_status} != {Scrambler_shutter_target}")
            print(msg)
            return False

        SimulCal_shutter_status = 'SimulCal' in shutter_list
        SimulCal_shutter_target = args.get('TimedShutter_SimulCal', False)
        if SimulCal_shutter_target != SimulCal_shutter_status:
            msg = (f"Final SimulCal timed shutter mismatch: "
                   f"{SimulCal_shutter_status} != {SimulCal_shutter_target}")
            print(msg)
            return False

        FF_Fiber_shutter_status = 'FF_Fiber' in shutter_list
        FF_Fiber_shutter_target = args.get('TimedShutter_FlatField', False)
        if FF_Fiber_shutter_target != FF_Fiber_shutter_status:
            msg = (f"Final FF_Fiber timed shutter mismatch: "
                   f"{FF_Fiber_shutter_status} != {FF_Fiber_shutter_target}")
            print(msg)
            return False

        Ca_HK_shutter_status = 'Ca_HK' in shutter_list
        CA_HK_shutter_target = args.get('TimedShutter_CaHK', False)
        if CA_HK_shutter_target != Ca_HK_shutter_status:
            msg = (f"Final Ca_HK timed shutter mismatch: "
                   f"{Ca_HK_shutter_status} != {CA_HK_shutter_target}")
            print(msg)
            return False

        print(f"    Done")
        return True

    @classmethod
    def add_cmdline_args(cls, parser, cfg=None):
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
