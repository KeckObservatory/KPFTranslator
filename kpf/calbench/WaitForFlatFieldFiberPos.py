import ktl

from ddoitranslatormodule.KPFTranslatorFunction import KPFTranslatorFunction
from .. import log


class WaitForFlatFieldFiberPos(KPFTranslatorFunction):
    '''Wait for the flat field fiber aperture via the `kpfcal.FF_FIBERPOS`
    keyword.
    
    Allowed Values:
    "Blank", "6 mm f/5", "7.5 mm f/4", "10 mm f/3", "13.2 mm f/2.3", "Open"
    '''
    @classmethod
    def pre_condition(cls, args, logger, cfg):
        target = args.get('FF_FiberPos', None)
        if target is None:
            return False
        allowed_values = ["Blank", "6 mm f/5", "7.5 mm f/4", "10 mm f/3",
                          "13.2 mm f/2.3", "Open"]
        return target in allowed_values

    @classmethod
    def perform(cls, args, logger, cfg):
        target = args.get('FF_FiberPos')
        timeout = cfg.get('times', 'nd_move_time', fallback=20)
        expr = f"($kpfcal.FF_FiberPos == '{target}')"
        success = ktl.waitFor(expr, timeout=timeout)
        if success is False:
            log.error(f"Timed out waiting for FF_FiberPos filter wheel")

    @classmethod
    def post_condition(cls, args, logger, cfg):
        target = args.get('FF_FiberPos')
        expr = f"($kpfcal.FF_FiberPos == '{target}')"
        success = ktl.waitFor(expr, timeout=0.1)
        return success

    @classmethod
    def add_cmdline_args(cls, parser, cfg=None):
        '''The arguments to add to the command line interface.
        '''
        from collections import OrderedDict
        args_to_add = OrderedDict()
        args_to_add['FF_FiberPos'] = {'type': str,
                                      'help': 'Wide flat aperture to use.'}
        parser = cls._add_args(parser, args_to_add, print_only=False)
        return super().add_cmdline_args(parser, cfg)