import time
import ktl

from kpf.KPFTranslatorFunction import KPFTranslatorFunction
from kpf import (log, KPFException, FailedPreCondition, FailedPostCondition,
                 FailedToReachDestination, check_input)


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

        kpf_expmeter['EXPMODE'].write('Single')
        biases = []
        for i in nExp:
            ready = kpf_expmeter['EXPSTATE'].waitFor("== 'Ready", timeout=60)
            if ready is not True:
                raise KPFError(f"Exposure Meter did not reach ready state")
            log.debug(f"Taking bias {i+1}/{nExp}")
            kpf_expmeter['EXPOSE'].write('Start')
            kpf_expmeter['EXPSTATE'].waitFor("== 'Ready", timeout=5)
            if ready is not True:
                raise KPFError(f"Exposure Meter did not reach ready state")
            lastfile = kpf_expmeter['FITSFILE'].read()
            biases.append(lastfile)

        # Set exposure meter back to operations settings
        log.info(f"Setting exposure meter to operational windowing")
        kpf_expmeter['BINX'].write(1)
        kpf_expmeter['BINY'].write(1)
        kpf_expmeter['TOP'].write(0)
        kpf_expmeter['LEFT'].write(1)
        kpf_expmeter['WIDTH'].write(651)
        kpf_expmeter['HEIGHT'].write(300)
        kpf_expmeter['OBJECT'].write('')

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
        return super().add_cmdline_args(parser, cfg)
