

import ktl

from ddoitranslatormodule.KPFTranslatorFunction import KPFTranslatorFunction


class ControlFoldMirror(KPFTranslatorFunction):
    '''Open or close the FIU hatch
    '''
    @classmethod
    def add_cmdline_args(cls, parser, cfg):
        """
        The arguments to add to the command line interface.
        """
        args_to_add = OrderedDict()
        args_to_add['destination'] = {'type': string,
                    'help': 'Desired fold mirror position: "in" or "out"'}

        parser = cls._add_args(parser, args_to_add, print_only=False)
        return super().add_cmdline_args(parser, cfg)

    @classmethod
    def pre_condition(cls, args, logger, cfg):
        destination = args.get('destination', '').strip()
        return destination.lower() in ['in', 'out']

    @classmethod
    def perform(cls, args, logger, cfg):
        destination = args.get('destination', '').strip()
        if destination.lower() in ['out']:
            FoldMirrorOut.execute({})
        elif destination.lower() in ['in']:
            FoldMirrorIn.execute({})

    @classmethod
    def post_condition(cls, args, logger, cfg):
        return True