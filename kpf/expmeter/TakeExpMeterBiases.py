import os
import time
from pathlib import Path

import ktl

from kpf.KPFTranslatorFunction import KPFTranslatorFunction
from kpf import (log, KPFException, FailedPreCondition, FailedPostCondition,
                 FailedToReachDestination, check_input)
from kpf.scripts import (register_script, obey_scriptrun, check_scriptstop,
                         add_script_log)
from kpf.expmeter.BuildMasterBias import BuildMasterBias
from kpf.calbench.SetCalSource import SetCalSource
from kpf.calbench.WaitForCalSource import WaitForCalSource
from kpf.spectrograph.ResetDetectors import ResetExpMeterDetector
from kpf.spectrograph.SetSourceSelectShutters import SetSourceSelectShutters
from kpf.spectrograph.WaitForReady import WaitForReady


class TakeExpMeterBiases(KPFTranslatorFunction):
    '''Take a set of bias frames for the exposure meter.

    Obeys kpfconfig.ALLOWSCHEDULEDCALS (will not run if that is set to No)

    Args:
    =====
    :nExp: The number of frames to take
    '''
    @classmethod
    @obey_scriptrun
    def pre_condition(cls, args, logger, cfg):
        check_input(args, 'nExp', allowed_types=[int])
        kpf_expmeter = ktl.cache('kpf_expmeter')
        # Check exposure meter enabled
        kpfconfig = ktl.cache('kpfconfig')
        EM_enabled = kpfconfig['EXPMETER_ENABLED'].read() == 'Yes'
        if EM_enabled == False:
            raise FailedPreCondition('Exposure meter is not enabled')
        # Check on exposure meter detector status
        if kpf_expmeter['COOLING'].read(binary=True) != True:
            raise FailedPreCondition('Exposure meter cooling is not On')
        cooltarg = kpf_expmeter['COOLTARG'].read(binary=True)
        currtemp = kpf_expmeter['CURRTEMP'].read(binary=True)
        deltaT = abs(currtemp-cooltarg)
        deltaT_threshold = cfg.getfloat('tolerances',
                                'expmeter_detector_temperature_tolerance',
                                fallback=0.5)
        if deltaT > deltaT_threshold:
            raise FailedPreCondition('Exposure meter not near target temperature')

    @classmethod
    @register_script(Path(__file__).name, os.getpid())
    @add_script_log(Path(__file__).name.replace(".py", ""))
    def perform(cls, args, logger, cfg):
        # Check if we're ok to take data
        allowscheduledcals = ktl.cache('kpfconfig', 'ALLOWSCHEDULEDCALS')
        if allowscheduledcals.read(binary=True) == False:
            log.warning(f'kpfconfig.ALLOWSCHEDULEDCALS=No. Not taking biases.')
            return []

        # Proceed with taking biases
        nExp = int(args.get('nExp'))
        log.info(f"Taking {nExp} exposure meter bias frames")
        kpf_expmeter = ktl.cache('kpf_expmeter')

        # Set exposure meter to full frame to take biases
        log.info(f"Setting exposure meter to full frame for biases")
        kpf_expmeter['BINX'].write(1)
        kpf_expmeter['BINY'].write(1)
        kpf_expmeter['TOP'].write(0)
        kpf_expmeter['LEFT'].write(0)
        kpf_expmeter['WIDTH'].write(1072)
        kpf_expmeter['HEIGHT'].write(1024)
        kpf_expmeter['EXPOSURE'].write(0.12)
        kpf_expmeter['OBJECT'].write('bias')
        kpf_expmeter['OBSERVER'].write('TakeExpMeterBiases')
        kpf_expmeter['EXPMODE'].write('Continuous')

        log.debug('Set Octagon to Home and close all source select shutters')
        SetCalSource.execute({'CalSource': 'Home'})
        WaitForReady.execute({})
        SetSourceSelectShutters.execute({})
        WaitForCalSource.execute({'CalSource': 'Home'})

        # Set TRIG_TARG to None, so that kpfassemble doesn't try
        # to pick up this data set
        trig_targ = ktl.cache('kpfexpose', 'TRIG_TARG')
        trig_targ.write('None')

        ready = kpf_expmeter['EXPSTATE'].waitFor("== 'Ready'", timeout=60)
        if ready is not True:
            raise KPFException(f"Exposure Meter did not reach ready state")

        # Start continuous exposures
        log.info(f"Starting continuous exposures")
        kpf_expmeter['EXPOSE'].write('Start')
        started = kpf_expmeter['EXPSTATE'].waitFor("!= 'Ready'", timeout=5)
        if started is not True:
            raise KPFException(f"Exposure Meter did not start exposures")
        
        got_frames = kpf_expmeter['SEQNUM'].waitFor(f"== {nExp}", timeout=2*nExp)
        if got_frames is not True:
            raise KPFException(f"Exposure Meter did not get all exposures")
        log.info(f"Stopping continuous exposures")
        kpf_expmeter['EXPOSE'].write('End')

        # Arbitrary wait to let file writing and DRP finish
        time.sleep(2)

        # Get FITSFILE
        lastfile = Path(kpf_expmeter['FITSFILE'].read())
        if lastfile.exists() is False:
            raise KPFException(f"Could not find file: {lastfile}")
        filename_parts = lastfile.name.split('.')
        filename_parts[1] = '*'
        biases = [f for f in lastfile.parent.glob('.'.join(filename_parts))]

        # Set exposure meter back to operations settings
        log.info(f"Setting exposure meter to operational windowing")
        kpf_expmeter['BINX'].write(1)
        kpf_expmeter['BINY'].write(1)
        kpf_expmeter['TOP'].write(0)
        kpf_expmeter['LEFT'].write(1)
        kpf_expmeter['WIDTH'].write(651)
        kpf_expmeter['HEIGHT'].write(300)
        kpf_expmeter['OBJECT'].write('')

        if args.get('combine', False) is True:
            BuildMasterBias.execute({'files': biases,
                                     'output': args.get('output'),
                                     'update': args.get('update')})

        return biases

    @classmethod
    def post_condition(cls, args, logger, cfg):
        expstate = ktl.cache('kpf_expmeter', 'EXPSTATE')
        expstate.monitor()
        timeout = 60
        ready = expstate.waitFor("== 'Ready'", timeout=timeout)
        if ready is not True:
            log.error(f'ExpMeter is not Ready after {timeout} s')
            log.warning(f'ExpMeter is {expstate.ascii}.  Resetting.')
            ResetExpMeterDetector.execute({})

    @classmethod
    def add_cmdline_args(cls, parser, cfg=None):
        parser.add_argument('nExp', type=int,
                            help="The number of frames to take")
        parser.add_argument("-c", "--combine", dest="combine",
                            default=False, action="store_true",
                            help="Combine the files in to a master bias?")
        parser.add_argument("--update", dest="update",
                            default=False, action="store_true",
                            help="Update the bias file in use with the newly generated file? (only used if --combine is used)")
        parser.add_argument("--output", dest="output", type=str,
                            default='',
                            help="The output combined bias file.")
        return super().add_cmdline_args(parser, cfg)
