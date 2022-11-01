import ktl

from ddoitranslatormodule.KPFTranslatorFunction import KPFTranslatorFunction


class ConfigureFIU(KPFTranslatorFunction):
    '''Set the FIU mode (kpffiu.MODE)
    
    Values: 0 None 1 Stowed 2 Alignment 3 Acquisition 4 Observing 5 Calibration
    '''
    @classmethod
    def pre_condition(cls, args, logger, cfg):
        dest = args.get('mode', None)
        if dest is None:
            return False
        allowed_modes = ['Stowed', 'Alignment', 'Acquisition', 'Observing',
                         'Calibration']
        return dest.lower() in [m.lower() for m in allowed_modes]

    @classmethod
    def perform(cls, args, logger, cfg):
        dest = args.get('mode')
        kpffiu = ktl.cache('kpffiu')
        kpffiu['MODE'].write(dest, wait=args.get('wait', True))

    @classmethod
    def post_condition(cls, args, logger, cfg):
        if args.get('wait', True) is True:
            dest = args.get('mode')
            expr = f"($kpffiu.mode == {dest})"
            cfg = cls._load_config(cls, cfg)
            timeout = cfg.get('times', 'fiu_fold_mirror_move_time', fallback=60)
            success = ktl.waitFor(expr, timeout=timeout)
            return success
        else:
            return True

    @classmethod
    def add_cmdline_args(cls, parser, cfg=None):
        '''The arguments to add to the command line interface.
        '''
        from collections import OrderedDict
        args_to_add = OrderedDict()
        args_to_add['mode'] = {'type': str,
                               'help': 'Desired mode (see kpffiu.MODE)'}
        parser = cls._add_args(parser, args_to_add, print_only=False)

        parser = cls._add_bool_arg(parser, 'wait',
            'Return only after move is finished?', default=True)

        return super().add_cmdline_args(parser, cfg)

