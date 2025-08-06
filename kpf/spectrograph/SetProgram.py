import time
import ktl

from kpf import log, cfg
from kpf.exceptions import *
from kpf.KPFTranslatorFunction import KPFFunction, KPFScript
from kpf.spectrograph.WaitForReady import WaitForReady


class SetProgram(KPFFunction):
    '''Sets the PROGNAME keyword for the science detectors in the kpfexpose
    keyword service.

    Args:
        progname (str): The program ID to set.

    KTL Keywords Used:

    - `kpfexpose.PROGNAME`
    '''
    @classmethod
    def pre_condition(cls, args):
        check_input(args, 'progname')

    @classmethod
    def perform(cls, args):
        PROGNAME = ktl.cache('kpfexpose', 'PROGNAME')
        prognameval = args.get('progname')
        log.debug('Waiting for kpfexpose to be ready')
        WaitForReady.execute({})
        log.info(f"Setting PROGNAME to '{prognameval}'")
        PROGNAME.write(prognameval)

    @classmethod
    def post_condition(cls, args):
        PROGNAME = ktl.cache('kpfexpose', 'PROGNAME')
        prognameval = args.get('progname')
        timeout = cfg.getfloat('times', 'kpfexpose_response_time', fallback=1)
        if PROGNAME.waitFor(f"== '{prognameval}'", timeout=timeout) != True:
            raise FailedToReachDestination(PROGNAME.read(), prognameval)

    @classmethod
    def add_cmdline_args(cls, parser):
        parser.add_argument('progname', type=str,
                            help='The PROGNAME keyword')
        return super().add_cmdline_args(parser)
