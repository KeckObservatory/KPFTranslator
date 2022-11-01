import ktl

from ddoitranslatormodule.KPFTranslatorFunction import KPFTranslatorFunction
from .FoldMirrorOut import FoldMirrorOut
from .FoldMirrorIn import FoldMirrorIn

class ControlFoldMirror(KPFTranslatorFunction):
    '''Insert or remove the FIU Cal Fold Mirror from the beam.
    '''
    @classmethod
    def pre_condition(cls, args, logger, cfg):
        destination = args.get('destination', '').strip()
        return destination.lower() in ['in', 'out']

    @classmethod
    def perform(cls, args, logger, cfg):
        destination = args.get('destination', '').strip()
        kpffiu = ktl.cache('kpffiu')
        kpffiu['FOLDNAM'].write(destination)

    @classmethod
    def post_condition(cls, args, logger, cfg):
        destination = args.get('destination', '').strip()
        cfg = cls._load_config(cls, cfg)
        timeout = cfg.get('times', 'fiu_fold_mirror_move_time', fallback=5)
        return ktl.waitFor(f'($kpffiu.foldnam == {destination})', timeout=timeout)

    @classmethod
    def add_cmdline_args(cls, parser, cfg=None):
        '''The arguments to add to the command line interface.
        '''
        from collections import OrderedDict
        args_to_add = OrderedDict()
        args_to_add['destination'] = {'type': str,
                    'help': 'Desired fold mirror position: "in" or "out"'}

        parser = cls._add_args(parser, args_to_add, print_only=False)
        return super().add_cmdline_args(parser, cfg)

