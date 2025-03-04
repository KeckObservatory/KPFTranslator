import time
import ktl

from kpf import log, cfg
from kpf.exceptions import *
from kpf.KPFTranslatorFunction import KPFFunction, KPFScript
from kpf.spectrograph.WaitForReady import WaitForReady


class SetProgram(KPFFunction):
    '''Sets the PROGNAME keyword for the science detectors in the kpfexpose
    keyword service.
    
    ARGS:
    =====
    :progname: `str` The program ID to set.
    '''
    @classmethod
    def pre_condition(cls, args):
        check_input(args, 'progname')

    @classmethod
    def perform(cls, args):
        kpfexpose = ktl.cache('kpfexpose')
        progname = args.get('progname')
        log.debug('Waiting for kpfexpose to be ready')
        WaitForReady.execute({})
        log.info(f"Setting PROGNAME to '{progname}'")
        kpfexpose['PROGNAME'].write(progname)
        time_shim = cfg.getfloat('times', 'kpfexpose_shim_time', fallback=0.1)
        time.sleep(time_shim)

    @classmethod
    def post_condition(cls, args):
        progname = args.get('progname')
        timeout = cfg.getfloat('times', 'kpfexpose_response_time', fallback=1)
        expr = f"($kpfexpose.PROGNAME == '{progname}')"
        success = ktl.waitFor(expr, timeout=timeout)
        if success is not True:
            prognamekw = ktl.cache('kpfexpose', 'PROGNAME')
            raise FailedToReachDestination(prognamekw.read(), progname)

    @classmethod
    def add_cmdline_args(cls, parser):
        parser.add_argument('progname', type=str,
                            help='The PROGNAME keyword')
        return super().add_cmdline_args(parser)
