import ktl

from kpf.KPFTranslatorFunction import KPFTranslatorFunction
from kpf import (log, KPFException, FailedPreCondition, FailedPostCondition,
                 FailedToReachDestination, check_input)


class ControlFoldMirror(KPFTranslatorFunction):
    '''Insert or remove the FIU Cal Fold Mirror from the beam.
    
    ARGS:
    =====
    :destination: The desired FIU fold mirror position name
    :wait: (bool) Wait for move to complete before returning? (default: True)
    '''
    @classmethod
    def pre_condition(cls, args, logger, cfg):
        destination = args.get('destination', '').strip()
        if destination.lower() not in ['in', 'out']:
            raise FailedPreCondition(f"Requested state {destination} is invalid")
        return True

    @classmethod
    def perform(cls, args, logger, cfg):
        destination = args.get('destination', '').strip()
        kpffiu = ktl.cache('kpffiu')
        kpffiu['FOLDNAM'].write(destination)

    @classmethod
    def post_condition(cls, args, logger, cfg):
        destination = args.get('destination', '').strip()
        timeout = cfg.get('times', 'fiu_fold_mirror_move_time', fallback=5)
        success = ktl.waitFor(f'($kpffiu.foldnam == {destination})', timeout=timeout)
        if success is not True:
            foldnam = ktl.cache('kpffiu', 'FOLDNAM')
            raise FailedToReachDestination(foldnam.read(), destination)

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

