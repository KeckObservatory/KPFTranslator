from time import sleep

import ktl

from ddoitranslatormodule.KPFTranslatorFunction import KPFTranslatorFunction
from .. import log


class SetTriggeredDetectors(KPFTranslatorFunction):
    '''Selects which cameras will be triggered by setting the
    `kpfexpose.TRIG_TARG` keyword value.
    '''
    @classmethod
    def pre_condition(cls, args, logger, cfg):
        return True

    @classmethod
    def perform(cls, args, logger, cfg):
        detector_list = []
        if args.get('TriggerRed', False) is True:
            detector_list.append('Red')
        if args.get('TriggerGreen', False) is True:
            detector_list.append('Green')
        if args.get('TriggerCaHK', False) is True:
            detector_list.append('Ca_HK')
        if args.get('TriggerExpMeter', False) is True:
            detector_list.append('ExpMeter')

        detectors_string = ','.join(detector_list)
        log.debug(f"  Setting triggered detectors to '{detectors_string}'")
        kpfexpose = ktl.cache('kpfexpose')
        kpfexpose['TRIG_TARG'].write(detectors_string)

    @classmethod
    def post_condition(cls, args, logger, cfg):
        kpfexpose = ktl.cache('kpfexpose')
        timeshim = cfg.get('times', 'kpfexpose_shim_time', fallback=0.01)
        sleep(timeshim)
        detectors = kpfexpose['TRIG_TARG'].read()
        detector_list = detectors.split(',')

        red_status = 'Red' in detector_list
        red_target = args.get('TriggerRed', False)
        if red_target != red_status:
            msg = (f"Final Red detector trigger mismatch: "
                   f"{red_status} != {red_target}")
            log.error(msg)
            return False

        green_status = 'Green' in detector_list
        green_target = args.get('TriggerGreen', False)
        if green_target != green_status:
            msg = (f"Final Green detector trigger mismatch: "
                   f"{green_status} != {green_target}")
            log.error(msg)
            return False

        CaHK_status = 'Ca_HK' in detector_list
        CaHK_target = args.get('TriggerCaHK', False)
        if CaHK_target != CaHK_status:
            msg = (f"Final Ca HK detector trigger mismatch: "
                   f"{CaHK_status} != {CaHK_target}")
            log.error(msg)
            return False

        return True

    @classmethod
    def add_cmdline_args(cls, parser, cfg=None):
        '''The arguments to add to the command line interface.
        '''
        parser = cls._add_bool_arg(parser, 'TriggerRed',
                                   'Trigger the Red detector?',
                                   default=False)
        parser = cls._add_bool_arg(parser, 'TriggerGreen',
                                   'Trigger the Green detector?',
                                   default=False)
        parser = cls._add_bool_arg(parser, 'TriggerCaHK',
                                   'Trigger the CaH&K detector?',
                                   default=False)
        parser = cls._add_bool_arg(parser, 'TriggerExpMeter',
                                   'Trigger the ExpMeter detector?',
                                   default=False)

        return super().add_cmdline_args(parser, cfg)
