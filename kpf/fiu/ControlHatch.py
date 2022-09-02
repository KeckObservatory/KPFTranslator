import ktl

from collections import OrderedDict
from CloseHatch import CloseHatch
from OpenHatch import OpenHatch

from ddoitranslatormodule.KPFTranslatorFunction import KPFTranslatorFunction


class ControlHatch(KPFTranslatorFunction):
    '''Open or close the FIU hatch
    '''
    @classmethod
    def add_cmdline_args(cls, parser, cfg=None):
        """
        The arguments to add to the command line interface.
        """
        args_to_add = OrderedDict()
        args_to_add['destination'] = {'type': str,
                                      'help': 'Desired hatch position: "open" or "closed"'}

        parser = cls._add_args(parser, args_to_add, print_only=False)
        return super().add_cmdline_args(parser, cfg)

    @classmethod
    def pre_condition(cls, args, logger, cfg):
        destination = args.get('destination', '').strip()
        return destination.lower() in ['close', 'closed', 'open']

    @classmethod
    def perform(cls, args, logger, cfg):
        destination = args.get('destination', '').strip()
        if destination.lower() in ['close', 'closed']:
            CloseHatch.execute({})
        elif destination.lower() in ['open']:
            OpenHatch.execute({})

    @classmethod
    def post_condition(cls, args, logger, cfg):
        return True