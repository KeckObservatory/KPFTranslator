import os
from pathlib import Path
import traceback
from logging import getLogger
from argparse import Namespace, ArgumentTypeError
import copy

from ddoitranslatormodule.BaseFunction import TranslatorModuleFunction

import ktl


class KPFTranslatorFunction(TranslatorModuleFunction):

    def _cfg_location(cls, args):
        """
        Return the fullpath + filename of default configuration file.

        :param args: <dict> The OB (or portion of OB) in dictionary form

        :return: <list> fullpath + filename of default configuration
        """
        cfg_path_base = os.path.dirname(os.path.abspath(__file__))

        inst = 'kpf'
        cfg = f"{cfg_path_base}/{inst}_inst_config.ini"
        config_files = [cfg]

        return config_files

    @classmethod
    def abort_execution(cls, args, logger, cfg):
        if cls.abortable != True:
            log.warning('Abort recieved, but this method is not abortable.')
            return False
        
        kpfconfig = ktl.cache('kpfconfig')
        this_file = Path(__file__).name.replace(".py", "")
        running_file = kpfconfig['SCRIPTNAME'].read()
        if this_file != running_file:
            log.warning(f'Abort recieved, but this method {this_file} is not '
                        f'the running script {running_file}.')
            return False

        log.warning('Abort recieved, setting kpfconfig.SCRTIPSTOP=Yes')
        kpfconfig['SCRIPTSTOP'].write('Yes')

    @classmethod
    def pre_condition(cls, args, logger, cfg):
        pass

    @classmethod
    def post_condition(cls, args, logger, cfg):
        pass

    @classmethod
    def execute(cls, args, logger=None, cfg=None):
        """Carries out this function in its entirety (pre and post conditions
           included)

        Parameters
        ----------
        args : dict
            The OB (or portion of OB) in dictionary form
        logger : DDOILoggerClient, optional
            The DDOILoggerClient that should be used. If none is provided, defaults to
            a generic name specified in the config, by default None
        cfg : filepath, optional
            File path to the config that should be used, by default None

        Returns
        -------
        bool
            True if execution was sucessful, False otherwise

        Raises
        ------
        DDOIArgumentsChangedException
            If any changes to the input arguments are detected, this exception
            is raised. Code within a TranslatorModuleFunction should **NOT**
            change the input arguments
        """
        if type(args) == Namespace:
            args = vars(args)
        elif type(args) != dict:
            msg = "argument type must be either Dict or Argparser.Namespace"
            raise DDOIInvalidArguments(msg)

        # Access the logger and pass it into each method
        if logger is None:
            logger = getLogger("")

        # read the config file
        cfg = cls._load_config(cls, cfg, args=args)

        # Store a copy of the initial args
        initial_args = copy.deepcopy(args)

        #################
        # PRE CONDITION #
        #################
        try:
            cls.pre_condition(args, logger, cfg)
        except Exception as e:
            logger.error(f"Exception encountered in pre-condition: {e}", exc_info=True)
            raise e

        args_diff = cls._diff_args(initial_args, args)
        if args_diff:
            logger.debug(f"Args changed after pre-condition")
            logger.debug(f"Before: {initial_args}")
            logger.debug(f"After: {args}")

        ###########
        # EXECUTE #
        ###########
        try:
            return_value = cls.perform(args, logger, cfg)
        except Exception as e:
            logger.error(f"Exception encountered in perform: {e}", exc_info=True)
            raise e

        args_diff = cls._diff_args(initial_args, args)
        if args_diff:
            logger.debug(f"Args changed after perform")
            logger.debug(f"Before: {initial_args}")
            logger.debug(f"After: {args}")

        ##################
        # POST CONDITION #
        ##################
        try:
            cls.post_condition(args, logger, cfg)
        except Exception as e:
            logger.error(f"Exception encountered in post-condition: {e}")
            logger.error(traceback.format_exc(), exc_info=True)
            raise e

        args_diff = cls._diff_args(initial_args, args)
        if args_diff:
            logger.debug(f"Args changed after post-condition")
            logger.debug(f"Before: {initial_args}")
            logger.debug(f"After: {args}")

        return return_value
