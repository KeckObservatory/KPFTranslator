from time import sleep

import ktl

from kpf.KPFTranslatorFunction import KPFTranslatorFunction
from kpf import (log, KPFException, FailedPreCondition, FailedPostCondition,
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
        pass

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
        if args.get('TriggerGuide', False) is True:
            detector_list.append('Guide')

        detectors_string = ','.join(detector_list)
        log.debug(f"Setting triggered detectors to '{detectors_string}'")
        kpfexpose = ktl.cache('kpfexpose')
        kpfexpose['TRIG_TARG'].write(detectors_string)
        shim_time = cfg.getfloat('times', 'kpfexpose_shim_time', fallback=0.1)
        sleep(shim_time)

    @classmethod
    def post_condition(cls, args, logger, cfg):
        kpfexpose = ktl.cache('kpfexpose')
        timeshim = cfg.getfloat('times', 'kpfexpose_shim_time', fallback=0.01)
        sleep(timeshim)
        detectors = kpfexpose['TRIG_TARG'].read()
        detector_list = detectors.split(',')

        detector_names = [('Red', 'TriggerRed'),
                          ('Green', 'TriggerGreen'),
                          ('Ca_HK', 'TriggerCaHK'),
                          ('ExpMeter', 'TriggerExpMeter'),
                          ('Guide', 'TriggerGuide'),
                          ]
        for detector in detector_names:
            detector_status = detector[0] in detector_list
            detector_target = args.get(detector[1], False)
            if detector_target != detector_status:
                raise FailedToReachDestination(detector_status, detector_target)

    @classmethod
    def add_cmdline_args(cls, parser, cfg=None):
        '''The arguments to add to the command line interface.
        '''
        parser.add_argument("--Red", "--red", "-r",
                            dest="TriggerRed",
                            default=False, action="store_true",
                            help="Trigger the Red detector during exposure?")
        parser.add_argument("--Green", "--green", "-g",
                            dest="TriggerGreen",
                            default=False, action="store_true",
                            help="Trigger the Green detector during exposure?")
        parser.add_argument("--CaHK", "--HK", "--cahk", "--hk",
                            dest="TriggerCaHK",
                            default=False, action="store_true",
                            help="Trigger the CaHK detector during exposure?")
        parser.add_argument("--ExpMeter", "--expmeter", "--EM", "--em",
                            dest="TriggerExpMeter",
                            default=False, action="store_true",
                            help="Trigger the ExpMeter detector during exposure?")
        parser.add_argument("--Guide", "--Guider", "--guide", "--guider", "--CRED2",
                            dest="TriggerGuide",
                            default=False, action="store_true",
                            help="Trigger the Guider detector during exposure?")
        return super().add_cmdline_args(parser, cfg)
