import ktl
from datetime import datetime, timedelta

from ddoitranslatormodule.KPFTranslatorFunction import KPFTranslatorFunction


class WaitForConfigureFIU(KPFTranslatorFunction):
    '''Wait for the FIU to reach specified mode (kpffiu.MODE)
    
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
        modes = kpffiu['MODE'].read().split(',')
        start = datetime.utcnow()
        move_times = [cfg.get('times', 'fiu_fold_mirror_move_time', fallback=30),
                      cfg.get('times', 'fiu_hatch_move_time', fallback=2)]
        end = start + timedelta(seconds=max(move_times))
        while dest not in modes and datetime.utcnow() <= end:
            sleep(1)
            modes = kpffiu['MODE'].read().split(',')

    @classmethod
    def post_condition(cls, args, logger, cfg):
        dest = args.get('mode')
        kpffiu = ktl.cache('kpffiu')
        modes = kpffiu['MODE'].read().split(',')
        return dest in modes

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
