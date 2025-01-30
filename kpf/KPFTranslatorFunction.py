import os
from pathlib import Path
import traceback
from logging import getLogger
import configparser
from argparse import Namespace, ArgumentTypeError

import ktl

from kpf import log, KPFException
from kpf.ObservingBlocks.ObservingBlock import ObservingBlock


class KPFFunction(object):
    '''A KPFFunction expects a dict of arguments as its input.
    '''
    instrument = 'kpf'

    @classmethod
    def _check_args(cls, args):
        if type(args) == Namespace:
            args = vars(args)
        elif type(args) not in [dict]:
            msg = "argument type must be either Dict or Argparser.Namespace"
            raise KPFException(msg)

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
        cls._check_args(args)

        # PRE CONDITION #
        try:
            cls.pre_condition(args)
        except Exception as e:
            log.error(f"Exception encountered in pre-condition: {e}", exc_info=True)
            raise e

        # PERFORM #
        try:
            return_value = cls.perform(args)
        except Exception as e:
            log.error(f"Exception encountered in perform: {e}", exc_info=True)
            raise e

        # POST CONDITION #
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


class KPFScript(KPFFunction):
    '''A KPFScript expects an OB data model as one if its inputs in
    addition to a dict of arguments.
    '''
    @classmethod
    def _check_OB(cls, OB):
        if type(OB) not in [dict, ObservingBlock]:
            msg = "OB argument type must be dict or ObservingBlock"
            raise KPFException(msg)

    @classmethod
    def execute(cls, args, OB=None):
        """Carries out this function in its entirety (pre and post conditions
           included)

        Parameters
        ----------
        args : dict
            The arguments in dictionary form
        """
        cls._check_args(args)
        if OB is not None:
            cls._check_OB(OB)

        # PRE CONDITION #
        try:
            cls.pre_condition(args, OB=OB)
        except Exception as e:
            log.error(f"Exception encountered in pre-condition: {e}", exc_info=True)
            raise e

        # PERFORM #
        try:
            return_value = cls.perform(args, OB=OB)
        except Exception as e:
            log.error(f"Exception encountered in perform: {e}", exc_info=True)
            raise e

        # POST CONDITION #
        try:
            cls.post_condition(args, OB=OB)
        except Exception as e:
            log.error(f"Exception encountered in post-condition: {e}")
            logger.error(traceback.format_exc(), exc_info=True)
            raise e

        return return_value
