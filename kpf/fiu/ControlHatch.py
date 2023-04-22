import ktl

from kpf.KPFTranslatorFunction import KPFTranslatorFunction
from kpf import (log, KPFException, FailedPreCondition, FailedPostCondition,
                 FailedToReachDestination, check_input)


class ControlHatch(KPFTranslatorFunction):
    '''Open or close the FIU hatch
    
    ARGS:
    =====
    :destination: The desired FIU hatch position name
    '''
    @classmethod
    def pre_condition(cls, args, logger, cfg):
        check_input(args, 'destination', allowed_values=['closed', 'open'])

    @classmethod
    def perform(cls, args, logger, cfg):
        destination = args.get('destination', '').strip()
        kpffiu = ktl.cache('kpffiu')
        kpffiu['HATCH'].write(destination)

    @classmethod
    def post_condition(cls, args, logger, cfg):
        destination = args.get('destination', '').strip()
        timeout = cfg.getfloat('times', 'fiu_hatch_move_time', fallback=1)
        success = ktl.waitFor(f'($kpffiu.hatch == {destination})', timeout=timeout)
        if success is not True:
            hatch = ktl.cache('kpffiu', 'HATCH')
            raise FailedToReachDestination(hatch.read(), destination)

    @classmethod
    def add_cmdline_args(cls, parser, cfg=None):
        '''The arguments to add to the command line interface.
        '''
        from collections import OrderedDict
        args_to_add = OrderedDict()
        args_to_add['destination'] = {'type': str,
                                'help': 'Desired hatch position: "open" or "closed"'}

        parser = cls._add_args(parser, args_to_add, print_only=False)
        return super().add_cmdline_args(parser, cfg)
