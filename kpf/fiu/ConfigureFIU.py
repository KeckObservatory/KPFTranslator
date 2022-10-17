import ktl

from collections import OrderedDict

from ddoitranslatormodule.KPFTranslatorFunction import KPFTranslatorFunction


class ConfigureFIU(KPFTranslatorFunction):
    '''Set the FIU mode (kpffiu.MODE)
    '''
    @classmethod
    def add_cmdline_args(cls, parser, cfg=None):
        """
        The arguments to add to the command line interface.
        """
        args_to_add = OrderedDict()
        args_to_add['mode'] = {'type': str,
                               'help': 'Desired mode (see kpffiu.MODE)'}

        parser = cls._add_args(parser, args_to_add, print_only=False)
        return super().add_cmdline_args(parser, cfg)

    @classmethod
    def pre_condition(cls, args, logger, cfg):
        return True

    @classmethod
    def perform(cls, args, logger, cfg):
        dest = args.get('mode')
        kpffiu = ktl.cache('kpffiu')
        kpffiu['MODE'].write(dest)

    @classmethod
    def post_condition(cls, args, logger, cfg):
        return True