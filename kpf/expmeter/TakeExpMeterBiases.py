import time
from pathlib import Path

import ktl

from kpf.KPFTranslatorFunction import KPFTranslatorFunction
from kpf import (log, KPFException, FailedPreCondition, FailedPostCondition,
                 FailedToReachDestination, check_input)
from kpf.expmeter.BuildMasterBias import BuildMasterBias


class TakeExpMeterBiases(KPFTranslatorFunction):
    '''Take a set of bias frames for the exposure meter.

    Obeys kpfconfig.ALLOWSCHEDULEDCALS (will not run if that is set to No)

    Args:
    =====
    :nExp: The number of frames to take
    '''
    @classmethod
    def pre_condition(cls, args, logger, cfg):
        check_input(args, 'nExp', allowed_types=[int])
        kpf_expmeter = ktl.cache('kpf_expmeter')
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
                                     'output': args.get('output')})

        return biases

    @classmethod
    def post_condition(cls, args, logger, cfg):
        pass

    @classmethod
    def add_cmdline_args(cls, parser, cfg=None):
        '''The arguments to add to the command line interface.
        '''
        parser.add_argument('nExp', type=int,
                            help="The number of frames to take")
        parser.add_argument("-c", "--combine", dest="combine",
                            default=False, action="store_true",
                            help="Combine the files in to a master bias?")
        parser.add_argument("--output", dest="output", type=str,
                            default='~/bias.fits',
                            help="The output combined bias file.")
        return super().add_cmdline_args(parser, cfg)
