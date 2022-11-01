import ktl

from ddoitranslatormodule.KPFTranslatorFunction import KPFTranslatorFunction
from .. import log


class SetND1(KPFTranslatorFunction):
    '''Set the filter in the ND1 filter wheel (the one at the output of the 
    octagon) via the `kpfcal.ND1POS` keyword.
    
    Allowed Values:
    "OD 0.1", "OD 1.0", "OD 1.3", "OD 2.0", "OD 3.0", "OD 4.0"
    '''
    @classmethod
    def pre_condition(cls, args, logger, cfg):
        target = args.get('CalND1', None)
        if target is None:
            return False
        allowed_values = ["OD 0.1", "OD 1.0", "OD 1.3", "OD 2.0", "OD 3.0",
                          "OD 4.0"]
        return target in allowed_values

    @classmethod
    def perform(cls, args, logger, cfg):
        target = args.get('CalND1')
        log.debug(f"Setting ND1POS to {target}")
        kpfcal = ktl.cache('kpfcal')
        kpfcal['ND1POS'].write(target, wait=args.get('wait', True))

    @classmethod
    def post_condition(cls, args, logger, cfg):
        target = args.get('CalND1')
        cfg = cls._load_config(cls, cfg)
        timeout = cfg.get('times', 'nd_move_time', fallback=20)
        expr = f"($kpfcal.ND1POS == '{target}')"
        success = ktl.waitFor(expr, timeout=timeout)
        return success

    @classmethod
    def add_cmdline_args(cls, parser, cfg=None):
        '''The arguments to add to the command line interface.
        '''
        from collections import OrderedDict
        args_to_add = OrderedDict()
        args_to_add['CalND1'] = {'type': str,
                                 'help': 'Filter to use'}
        parser = cls._add_args(parser, args_to_add, print_only=False)

        parser = cls._add_bool_arg(parser, 'wait',
            'Return only after move is finished?', default=True)

        return super().add_cmdline_args(parser, cfg)

