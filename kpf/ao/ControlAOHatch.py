from collections import OrderedDict

import ktl

from ddoitranslatormodule.KPFTranslatorFunction import KPFTranslatorFunction
from .. import log
from .CloseAOHatch import CloseAOHatch
from .OpenAOHatch import OpenAOHatch


class ControlAOHatch(KPFTranslatorFunction):
    '''Control the AO Hatch
    '''
    @classmethod
    def pre_condition(cls, args, logger, cfg):
        destination = args.get('destination', '').strip()
        return destination.lower() in ['close', 'open']

    @classmethod
    def perform(cls, args, logger, cfg):
        destination = args.get('destination', '').strip()
        ao = ktl.cache('ao')
        log.debug(f"Setting AO Hatch to {destination}")
        ao['aohatchcmd'].write(destination)

    @classmethod
    def post_condition(cls, args, logger, cfg):
        destination = args.get('destination', '').strip()
        return ktl.waitfor(f'($ao.AOHATCHSTS == {destination})', timeout=30)

    @classmethod
    def add_cmdline_args(cls, parser, cfg=None):
        args_to_add = OrderedDict()
        args_to_add['destination'] = {'type': str,
                                'help': 'Desired hatch position: "open" or "closed"'}

        parser = cls._add_args(parser, args_to_add, print_only=False)
        return super().add_cmdline_args(parser, cfg)
