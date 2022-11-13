import ktl

from ddoitranslatormodule.KPFTranslatorFunction import KPFTranslatorFunction
from .. import (KPFException, FailedPreCondition, FailedPostCondition,
                FailedToReachDestination, check_input)


class SetProgram(KPFTranslatorFunction):
    '''Sets the PROGNAME keyword for the science detectors in the kpfexpose
    keyword service.
    
    ARGS:
    progname - The program ID to set.
    '''
    @classmethod
    def pre_condition(cls, args, logger, cfg):
        check_input(args, 'progname')
        return True

    @classmethod
    def perform(cls, args, logger, cfg):
        kpfexpose = ktl.cache('kpfexpose')
        progname = args.get('progname')
        log.debug(f"Setting PROGNAME to '{progname}'")
        kpfexpose['PROGNAME'].write(progname)

    @classmethod
    def post_condition(cls, args, logger, cfg):
        progname = args.get('progname')
        timeout = cfg.get('times', 'kpfexpose_timeout', fallback=0.01)
        expr = f"($kpfexpose.PROGNAME == '{progname}')"
        success = ktl.waitFor(expr, timeout=timeout)
        if success is not True:
            prognamekw = ktl.cache('kpfexpose', 'PROGNAME')
            raise FailedToReachDestination(prognamekw.read(), progname)

    @classmethod
    def add_cmdline_args(cls, parser, cfg=None):
        '''The arguments to add to the command line interface.
        '''
        from collections import OrderedDict
        args_to_add = OrderedDict()
        args_to_add['progname'] = {'type': str,
                                   'help': 'The PROGNAME keyword.'}
        parser = cls._add_args(parser, args_to_add, print_only=False)
        return super().add_cmdline_args(parser, cfg)
