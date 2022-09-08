from pathlib import Path

import ktl

from ddoitranslatormodule.KPFTranslatorFunction import KPFTranslatorFunction


class GuiderOutdir(KPFTranslatorFunction):
    '''Print the value of the kpfguide.OUTDIR keyword to STDOUT
    '''
    @classmethod
    def pre_condition(cls, args, logger, cfg):
        return True

    @classmethod
    def perform(cls, args, logger, cfg):
        newoutdir = args.get('outdir', None)
        if newoutdir is not None:
            newoutdir = Path(newoutdir).expanduser().absolute()
            kpfguide = ktl.cache('kpfguide')
            kpfguide['OUTDIR'].write(f"{newoutdir}")

    @classmethod
    def post_condition(cls, args, logger, cfg):
        return True

    @classmethod
    def add_cmdline_args(cls, parser, cfg=None):
        """
        The arguments to add to the command line interface.
        """
        args_to_add = OrderedDict()
        args_to_add['outdir'] = {'type': str,
                                 'help': 'The desired output path.'}

        parser = cls._add_args(parser, args_to_add, print_only=False)
        return super().add_cmdline_args(parser, cfg)
