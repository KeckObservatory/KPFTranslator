

import ktl

from ddoitranslatormodule.KPFTranslatorFunction import KPFTranslatorFunction
from .. import log


class SetObject(KPFTranslatorFunction):
    '''Sets the OBJECT keyword for the science detectors in the kpfexpose
    keyword service.
    '''
    @classmethod
    def pre_condition(cls, args, logger, cfg):
        obj = args.get('object', None)
        if obj is None:
            return False
        return True

    @classmethod
    def perform(cls, args, logger, cfg):
        kpfexpose = ktl.cache('kpfexpose')
        obj = args.get('object')
        log.debug(f"Setting OBJECT time to '{obj}'")
        kpfexpose['OBJECT'].write(obj)

    @classmethod
    def post_condition(cls, args, logger, cfg):
        obj = args.get('object')
        timeout = cfg.get('times', 'kpfexpose_timeout', fallback=0.01)
        expr = (f"($kpfexpose.OBJECT == '{obj}')"
        success = ktl.waitFor(expr, timeout=timeout)
        return success

    @classmethod
    def add_cmdline_args(cls, parser, cfg=None):
        args_to_add = OrderedDict()
        args_to_add['object'] = {'type': str,
                                 'help': 'The OBJECT keyword.'}

        parser = cls._add_args(parser, args_to_add, print_only=False)
        return super().add_cmdline_args(parser, cfg)