

import ktl
from ddoitranslatormodule.BaseFunction import TranslatorModuleFunction
from ddoitranslatormodule.DDOIExceptions import *

from ..utils import *


class SetExptime(TranslatorModuleFunction):
    '''Sets the exposure time for the science detectors in the kpfexpose
    keyword service.
    '''
    def __init__(self):
        super().__init__()

    @classmethod
    def add_cmdline_args(cls, parser, cfg=None):
        # read the config file
        cfg = cls._load_config(cls, cfg)
        cls.key_exptime = cls._config_param(cfg, 'ob_keys', 'exptime')
        args_to_add = OrderedDict([
            (cls.key_exptime, {'type': float,
                                 'help': 'The exposure time in seconds.'}),
        ])
        parser = cls._add_args(parser, args_to_add, print_only=False)

        return super().add_cmdline_args(parser, cfg)

    @classmethod
    def pre_condition(cls, args, logger, cfg):
        print("Pre condition")
        return True

    @classmethod
    def perform(cls, args, logger, cfg):
        exptime = args.get('exptime', None)
        if exptime is not None:
            kpfexpose = ktl.cache('kpfexpose')
            exptime_value = kpfexpose['EXPOSURE'].read()
            if abs(exptime_value - exptime) > 0.1:
                msg = (f"Final exposure time mismatch: "
                       f"{exptime_value:.1f} != {exptime:.1f}")
                print(msg)
                raise KPFError(msg)
        print('    Done')

    @classmethod
    def post_condition(cls, args, logger, cfg):
        print("Post condition")
        return True
