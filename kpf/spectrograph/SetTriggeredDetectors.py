from time import sleep

import ktl

from kpf import log, cfg
from kpf.exceptions import *
from kpf.KPFTranslatorFunction import KPFFunction, KPFScript


class SetTriggeredDetectors(KPFFunction):
    '''Selects which cameras will be triggered by setting the
    `kpfexpose.TRIG_TARG` keyword value.
    
    ARGS:
    =====
    :TriggerRed: `bool` Trigger the Red detector? (default=False)
    :TriggerGreen: `bool` Trigger the Green detector? (default=False)
    :TriggerCaHK: `bool` Trigger the CaH&K detector? (default=False)
    :TriggerExpMeter: `bool` Trigger the ExpMeter detector? (default=False)
    '''
    @classmethod
    def pre_condition(cls, args):
        pass

    @classmethod
    def perform(cls, args):
        kpfconfig = ktl.cache('kpfconfig')
        detector_list = []
        if args.get('TriggerRed', False) is True:
            if kpfconfig['RED_ENABLED'].read(binary=True) == False:
                log.warning(f'Red detector is not enabled')
            else:
                detector_list.append('Red')
        if args.get('TriggerGreen', False) is True:
            if kpfconfig['GREEN_ENABLED'].read(binary=True) == False:
                log.warning(f'Green detector is not enabled')
            else:
                detector_list.append('Green')
        if args.get('TriggerCaHK', False) is True:
            if kpfconfig['CA_HK_ENABLED'].read(binary=True) == False:
                log.warning(f'Ca HK detector is not enabled')
            else:
                detector_list.append('Ca_HK')
        if args.get('TriggerExpMeter', False) is True:
            if kpfconfig['EXPMETER_ENABLED'].read(binary=True) == False:
                log.warning(f'ExpMeter detector is not enabled')
            else:
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
    def post_condition(cls, args):
        kpfconfig = ktl.cache('kpfconfig')
        kpfexpose = ktl.cache('kpfexpose')
        timeshim = cfg.getfloat('times', 'kpfexpose_shim_time', fallback=0.1)
        sleep(timeshim)
        detectors = kpfexpose['TRIG_TARG'].read()
        detector_list = detectors.split(',')
        detector_names = [('Red', 'TriggerRed'),
                          ('Green', 'TriggerGreen'),
                          ('Ca_HK', 'TriggerCaHK'),
                          ('ExpMeter', 'TriggerExpMeter'),
#                           ('Guide', 'TriggerGuide'),
                          ]
        # Don't check on guide because there is no enabled keyword for it
        for detector in detector_names:
            detector_status = detector[0] in detector_list
            enabled = kpfconfig[f'{detector[0].upper()}_ENABLED'].read(binary=True)
            detector_target = args.get(detector[1], False) and enabled
            if detector_target != detector_status:
                raise FailedToReachDestination(detector_status, detector_target)

    @classmethod
    def add_cmdline_args(cls, parser):
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
        return super().add_cmdline_args(parser)
