import os
from pathlib import Path
import traceback
from logging import getLogger
import configparser
from argparse import Namespace, ArgumentTypeError

import ktl

from kpf import log, KPFException


class KPFTranslatorFunction(object):

    instrument = 'kpf'

    def _load_config(cls):
        config_files = [Path(__file__).parent / f'{cls.instrument}_inst_config.ini']
        config = configparser.ConfigParser(inline_comment_prefixes=(';','#',))
        config.read(config_files)
        return config

    @classmethod
    def pre_condition(cls, args):
        pass

    @classmethod
    def post_condition(cls, args):
        pass

    @classmethod
    def perform(cls, args):
        pass

    @classmethod
    def execute(cls, args):
        """Carries out this function in its entirety (pre and post conditions
           included)

        Parameters
        ----------
        args : dict
            The arguments in dictionary form
        """
        if type(args) == Namespace:
            args = vars(args)
        elif type(args) != dict:
            msg = "argument type must be either Dict or Argparser.Namespace"
            raise KPFException(msg)

        # read the config file
        cfg = cls._load_config(cls)

        #################
        # PRE CONDITION #
        #################
        try:
            cls.pre_condition(args)
        except Exception as e:
            log.error(f"Exception encountered in pre-condition: {e}", exc_info=True)
            raise e

        ###########
        # EXECUTE #
        ###########
        try:
            return_value = cls.perform(args)
        except Exception as e:
            log.error(f"Exception encountered in perform: {e}", exc_info=True)
            raise e

        ##################
        # POST CONDITION #
        ##################
        try:
            cls.post_condition(args)
        except Exception as e:
            log.error(f"Exception encountered in post-condition: {e}")
            logger.error(traceback.format_exc(), exc_info=True)
            raise e

        return return_value


    """
    Command line Argument Section for use with CLI (Command Line Interface)
    
        parser = argparse.ArgumentParser()
        args = Function.add_cmdline_args(parser)
        result = Function.execute(args)
    """
    @classmethod
    def add_cmdline_args(cls, parser):
        """
        The arguments to add to the command line interface.

        :param parser: <ArgumentParser>
            the instance of the parser to add the arguments to .

        :return: <ArgumentParser>
        """
        # add: return super().add_cmdline_args(parser) to the end of extended method
        parser.add_argument('-h', '--help', action='help', default='==SUPPRESS==',
                            help='show this help message and exit')

        return parser
