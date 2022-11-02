import ktl

from ddoitranslatormodule.KPFTranslatorFunction import KPFTranslatorFunction


class SetTipTiltCalculations(KPFTranslatorFunction):
    '''
    '''
    @classmethod
    def pre_condition(cls, args, logger, cfg):
        gain = args.get('calculations', None)
        if gain is None:
            return False
        return gain in ['Active', 'Inactive', '1', '0', 1, 0]

    @classmethod
    def perform(cls, args, logger, cfg):
        calculations = args.get('calculations')
        tiptiltcalc = ktl.cache('kpfguide', 'TIPTILT')
        tiptiltcalc.write(calculations)

    @classmethod
    def post_condition(cls, args, logger, cfg):
        calculations = args.get('calculations')
        timeout = cfg.get('times', 'tip_tilt_move_time', fallback=0.1)
        expr = f"($kpfguide.TIPTILT == {calculations}) "
        success = ktl.waitFor(expr, timeout=timeout)
        return success

    @classmethod
    def add_cmdline_args(cls, parser, cfg=None):
        '''The arguments to add to the command line interface.
        '''
        from collections import OrderedDict
        args_to_add = OrderedDict()
        args_to_add['calculations'] = {'type': str,
                                       'help': 'Calulations "Active" or "Inactive"'}
        parser = cls._add_args(parser, args_to_add, print_only=False)
        return super().add_cmdline_args(parser, cfg)
