

import ktl
from ddoitranslatormodule.BaseInstrument import InstrumentBase
from ddoitranslatormodule.DDOIExceptions import *

from ..utils import *


class SetExptime(InstrumentBase):
    '''Sets the exposure time for the science detectors in the kpfexpose
    keyword service.
    '''
    @classmethod
    def add_cmdline_args(cls, parser, cfg):
        """
        The arguments to add to the command line interface.

        :param parser: <ArgumentParser>
            the instance of the parser to add the arguments to .
        :param cfg: <class 'configparser.ConfigParser'> the config file parser.

        :return: <ArgumentParser>
        """
        args_to_add = OrderedDict()
        args_to_add['exptime'] = {'type': float,
                                  'help': 'The exposure time in seconds.'}

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
