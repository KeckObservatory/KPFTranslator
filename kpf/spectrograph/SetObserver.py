

import ktl

from ddoitranslatormodule.KPFTranslatorFunction import KPFTranslatorFunction
from .. import log


class SetObserver(KPFTranslatorFunction):
    '''Sets the OBSERVER keyword for the science detectors in the kpfexpose
    keyword service.
    '''
    @classmethod
    def pre_condition(cls, args, logger, cfg):
        observer = args.get('observer', None)
        if observer is None:
            return False
        return True

    @classmethod
    def perform(cls, args, logger, cfg):
        kpfexpose = ktl.cache('kpfexpose')
        observer = args.get('observer')
        log.debug(f"Setting OBSERVER to '{observer}'")
        kpfexpose['OBSERVER'].write(observer)

    @classmethod
    def post_condition(cls, args, logger, cfg):
        observer = args.get('observer')
        timeout = cfg.get('times', 'kpfexpose_timeout', fallback=0.01)
        expr = (f"($kpfexpose.OBSERVER == '{observer}')"
        success = ktl.waitFor(expr, timeout=timeout)
        return success

    @classmethod
    def add_cmdline_args(cls, parser, cfg=None):
        args_to_add = OrderedDict()
        args_to_add['observer'] = {'type': str,
                                   'help': 'The OBSERVER keyword.'}

        parser = cls._add_args(parser, args_to_add, print_only=False)
        return super().add_cmdline_args(parser, cfg)
