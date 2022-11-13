from time import sleep

import ktl

from ddoitranslatormodule.KPFTranslatorFunction import KPFTranslatorFunction
from .. import (KPFException, FailedPreCondition, FailedPostCondition,
                FailedToReachDestination, check_input)


class SetTriggeredDetectors(KPFTranslatorFunction):
    '''Selects which cameras will be triggered by setting the
    `kpfexpose.TRIG_TARG` keyword value.
    
    ARGS:
    TriggerRed (bool) - Trigger the Red detector? (default=False)
    TriggerGreen (bool) - Trigger the Green detector? (default=False)
    TriggerCaHK (bool) - Trigger the CaH&K detector? (default=False)
    TriggerExpMeter (bool) - Trigger the ExpMeter detector? (default=False)
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

        detector_names = [('Red', 'TriggerRed'),
                          ('Green', 'TriggerGreen'),
                          ('Ca_HK', 'TriggerCaHK')]
        for detector in detector_names:
            detector_status = detector[0] in detector_names
            detector_target = args.get(detector[1], False)
            if detector_target != detector_status:
                raise FailedToReachDestination(detector_status, detector_target)

    @classmethod
    def add_cmdline_args(cls, parser, cfg=None):
        '''The arguments to add to the command line interface.
        '''
        parser = cls._add_bool_arg(parser, 'TriggerRed', default=False,
                                   'Trigger the Red detector?')
        parser = cls._add_bool_arg(parser, 'TriggerGreen', default=False,
                                   'Trigger the Green detector?')
        parser = cls._add_bool_arg(parser, 'TriggerCaHK', default=False,
                                   'Trigger the CaH&K detector?')
        parser = cls._add_bool_arg(parser, 'TriggerExpMeter', default=False,
                                   'Trigger the ExpMeter detector?')
        return super().add_cmdline_args(parser, cfg)
