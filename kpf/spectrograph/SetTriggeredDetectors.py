from time import sleep
import numpy as np

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
        TRIG_TARG = ktl.cache('kpfexpose', 'TRIG_TARG')
        TRIG_TARG.write(detectors_string)

    @classmethod
    def post_condition(cls, args):
        kpfconfig = ktl.cache('kpfconfig')
        TRIG_TARG = ktl.cache('kpfexpose', 'TRIG_TARG')
        TRIG_TARG.monitor()
        detector_names = [('Red', 'TriggerRed',
                           kpfconfig[f'RED_ENABLED'].read(binary=True)),
                          ('Green', 'TriggerGreen',
                           kpfconfig[f'GREEN_ENABLED'].read(binary=True)),
                          ('Ca_HK', 'TriggerCaHK',
                           kpfconfig[f'CA_HK_ENABLED'].read(binary=True)),
                          ('ExpMeter', 'TriggerExpMeter',
                           kpfconfig[f'EXPMETER_ENABLED'].read(binary=True)),
                          ]
        detector_tests = [False]
        timeshim = cfg.getfloat('times', 'kpfexpose_shim_time', fallback=0.01)
        total_time = 0
        while np.all(detector_tests) != True and total_time < 0.25:
            detector_tests = []
            for detector in detector_names:
                if args.get(detector[1], False) and detector[2]:
                    detector_tests.append(detector[0] in TRIG_TARG.ascii.split(','))
            sleep(timeshim)
            total_time += timeshim
        if np.all(detector_tests) != True:
            raise FailedToReachDestination(TRIG_TARG.ascii, 'TBD')

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
