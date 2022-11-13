import ktl

from ddoitranslatormodule.KPFTranslatorFunction import KPFTranslatorFunction
from .. import log


class SetExptime(KPFTranslatorFunction):
    '''Sets the exposure time for the science detectors in the kpfexpose
    keyword service.
    
    Args:
    Exptime - The exposure time in seconds
    '''
    @classmethod
    def pre_condition(cls, args, logger, cfg):
        exptime = args.get('Exptime', None)
        if exptime is None:
            return False
        return (exptime >= 0)

    @classmethod
    def perform(cls, args, logger, cfg):
        kpfexpose = ktl.cache('kpfexpose')
        exptime = args.get('Exptime')
        log.debug(f"Setting exposure time to {exptime:.3f}")
        kpfexpose['EXPOSURE'].write(exptime)

    @classmethod
    def post_condition(cls, args, logger, cfg):
        kpfexpose = ktl.cache('kpfexpose')
        exptime = args.get('Exptime')
        tol = cfg.get('tolerances', 'kpfexpose_exptime_tolerance', fallback=0.01)
        timeout = cfg.get('times', 'kpfexpose_timeout', fallback=0.01)
        expr = (f"($kpfexpose.EXPOSURE >= {exptime-tol}) and "
                f"($kpfexpose.EXPOSURE <= {exptime+tol})")
        success = ktl.waitFor(expr, timeout=timeout)
        return success

    @classmethod
    def add_cmdline_args(cls, parser, cfg=None):
        '''The arguments to add to the command line interface.
        '''
        from collections import OrderedDict
        args_to_add = OrderedDict()
        args_to_add['Exptime'] = {'type': float,
                                  'help': 'The exposure time in seconds.'}

        parser = cls._add_args(parser, args_to_add, print_only=False)
        return super().add_cmdline_args(parser, cfg)
