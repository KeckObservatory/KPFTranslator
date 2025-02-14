import os
import stat
import sys
import importlib
import traceback
import configparser
from pathlib import Path
from argparse import ArgumentParser, ArgumentError
import logging
from datetime import datetime, timedelta
import yaml
from typing import Dict, List, Tuple

from kpf.KPFTranslatorFunction import KPFFunction, KPFScript
from kpf.ObservingBlocks.ObservingBlock import ObservingBlock


class LinkingTable():
    """Class storing the contents of a linking table
    """

    def __init__(self, filename, logger):
        """Create the LinkingTable

        Parameters
        ----------
        filename : str
            Filepath to the linking table
        
        logger : logging.Logger
            Python logging instance
        """

        self.logger = logger
        logger.debug(f"Linking Table: Loading file at {filename}")

        try:
            with open(filename) as f:
                self.cfg = yaml.load(f, Loader=yaml.FullLoader)
        except:
            logger.error(f"Linking Table: Unable to load {filename}")
            return
        self.prefix = self.cfg['common']['prefix']
        self.suffix = self.cfg['common']['suffix']
        self.links = self.cfg['links']
        logger.debug(f"Linking Table: Loading prefix: {self.prefix}, suffix: {self.suffix}, with {len(self.links)} links.")

    def get_entry_points(self) -> List[str]:
        """Gets a list of all the entry points listed in the linking table

        Returns
        -------
        List[str]
            List of all entry points (keys) in the linking table
        """
        eps = [key for key in self.links]
        return eps

    def print_entry_points(self, prefix="") -> None:
        """Prints out all the entry points listed in the linking table

        Parameters
        ----------
        prefix : str, optional
            String to be prepended to each line, by default ""
        """
        for i in self.get_entry_points():
            print(prefix + i)

    def get_link(self, entry_point) -> str:
        """Gets the full import string from the linking table for a given entry
        point (key)

        Parameters
        ----------
        entry_point : str
            Entry point (key) to get

        Returns
        -------
        str
            Python import string for the requested function

        Raises
        ------
        KeyError
            Raised if the linking table does not have an entry matching entry_point
        """
        if entry_point not in self.links:
            raise KeyError(f"Failed to find {entry_point} in table")
        output = ""
        if self.prefix:
            output += self.prefix + "."
        output += self.links[entry_point]["cmd"]
        if self.suffix:
            output += "." + self.suffix
        return output

def get_linked_function(linking_tbl, key, logger):
    """Searches a linking table for a given key, and attempts to fetch the
    associated python module

    Parameters
    ----------
    linking_tbl : LinkingTable
        Linking Table that should be searched
    key : str
        CLI function being searched for

    Returns
    -------
    Tuple[class, str]
        The class matching the given key, and the module path string needed to
        import it. If no such module is found, returns (None, None)
    """

    # Check to see if there is an entry matching the given key
    if key not in linking_tbl.get_entry_points():
        raise Exception(f"Unable to find an import for {key}")
    link = linking_tbl.get_link(key)

    # Get only the module path
    link_elements = link.split(".")
    # Get only the module import string
    module_str = ".".join(link_elements[:-1])
    # Get only the class name
    class_str = link_elements[-1]

    try:
        # Try to import the package from the string in the linking table
        mod = importlib.import_module(module_str)

        try:
#             return getattr(mod, class_str), default_args, link
            return getattr(mod, class_str), link
        except:
            logger.error("Failed to find a class with a perform method")
            logger.error(traceback.format_exc())
            return None, None

    except ImportError as e:
        logger.error(f"Failed to import {module_str}")
        logger.error(traceback.format_exc())
        return None, None

def create_logger():
    log = logging.getLogger('cli_interface')
    log.setLevel(logging.DEBUG)
    ## Set up console output
    LogConsoleHandler = logging.StreamHandler()
    LogConsoleHandler.setLevel(logging.INFO)
    LogFormat = logging.Formatter('%(asctime)s:%(filename)s:%(levelname)8s: %(message)s')
    LogConsoleHandler.setFormatter(LogFormat)
    log.addHandler(LogConsoleHandler)
    ## Set up file output
    utnow = datetime.utcnow()
    date = utnow-timedelta(days=1)
    date_str = date.strftime('%Y%b%d').lower()
    logdir = Path(f"/s/sdata1701/KPFTranslator_logs/{date_str}/cli_logs")
    if logdir.exists() is False:
        logdir.mkdir(mode=0o777, parents=True)
    if not os.stat(logdir.parent).st_mode & stat.S_IWOTH:
#         print(f"Fixing permissions on {logdir.parent}")
        # Try to set permissions on the date directory
        # necessary because the mode input to mkdir is modified by umask
        try:
            os.chmod(logdir.parent, 0o777)
        except OSError as e:
            pass
    if not os.stat(logdir).st_mode & stat.S_IWOTH:
#         print(f"Fixing permissions on {logdir}")
        # Try to set permissions on the cli_logs directory
        # necessary because the mode input to mkdir is modified by umask
        try:
            os.chmod(logdir, 0o777)
        except OSError as e:
            pass
    
    LogFileName = logdir / 'cli_interface.log'
    LogFileHandler = logging.FileHandler(LogFileName)
    LogFileHandler.setLevel(logging.DEBUG)
    LogFileHandler.setFormatter(LogFormat)
    log.addHandler(LogFileHandler)
    # Try to change permissions on file in case they are bad
    try:
        os.chmod(LogFileName, 0o666)
    except OSError as e:
        pass

    return log


def main(table_loc, parsed_args, function_args, kpfdo_parser):

    # Logging
    logger = create_logger()
    logger.debug("Created logger")
    invocation = ' '.join(sys.argv)
    logger.debug(f"Invocation: {invocation}")

    # Build the linking table
    table_loc = Path(table_loc)
    if not table_loc.suffix in [".yml", ".yaml"]:
        logger.error("Linking table must be a .yml or .yaml file! Exiting...")
        sys.exit(1)
    if not table_loc.exists():
        logger.error(f"Failed to find a linking table at {str(table_loc)}. Exiting...")
        sys.exit(1)
    linking_tbl = LinkingTable(table_loc, logger)

    # Handle list
    if parsed_args.list:
        logger.debug("Printing list...")
        linking_tbl.print_entry_points()
        return

    if parsed_args.help is True and len(function_args) < 1:
        logger.debug('Printing kpfdo help')
        kpfdo_parser.print_help()
        return

    if len(function_args) < 1:
        logger.debug('No function given and no options invoked')
        kpfdo_parser.print_help()
        return

    # Get the function
    try:
        logger.debug(f"Fetching {function_args[0]}...")
        function, mod_str = get_linked_function(
            linking_tbl, function_args[0], logger)
        logger.debug(f"Found at {mod_str}")
    except ImportError as e:
        logger.error("Found translator module, but failed to import it")
        logger.error(e)
        logger.error(traceback.format_exc())
        sys.exit(1)
    except TypeError as e:
        logger.error(traceback.format_exc())
        sys.exit(1)
    except Exception as e:
        logger.error("Unexpected exception encountered in CLI:")
        logger.error(e)
        logger.error(traceback.format_exc())
        sys.exit(1)

    # Build an ArgumentParser and attach the function's arguments
    final_args = function_args[1:]
    parser = ArgumentParser(add_help=False)
    logger.debug(f"Adding CLI args to parser")
    parser = function.add_cmdline_args(parser)
    logger.debug("Parsing function arguments...")

    script = function.__mro__[1] == KPFScript
    if script is True:
        logger.debug('Requested function is a script')
        parser.add_argument("-f", "--file", dest="file", type=str,
            help="The OB file to run.")
        parser.add_argument("-d", "--db", dest="dbid", type=str,
            help="The unique database ID of the OB to run.")

    if parsed_args.help is True:
        print('    '+function.__doc__)
        help_str = parser.format_help()
        help_str = help_str.replace('usage: kpfdo', f'usage: kpfdo {function_args[0]}')
        print(help_str)
        return

    try:
        # Append these parsed args onto whatever was (or wasn't)
        # found in the input file (i.e. if -f was used)
        parsed_func_args = vars(parser.parse_args(final_args))
        logger.debug("Parsed.")
    except ArgumentError as e:
        logger.error("Failed to parse arguments!")
        logger.error(e)
        logger.error(traceback.format_exc())
        sys.exit(1)

    if script is True:
        OB = None
        input_file = parsed_func_args.get('file', None)
        if input_file is not None:
            logger.debug(f"Found an input file: {input_file}")
            # Load the file
            if ".yml" in input_file or ".yaml" in input_file:
                import yaml
                with open(input_file, "r") as stream:
                    try:
                        OBdict = yaml.safe_load(stream)
                    except yaml.YAMLError as e:
                        logger.error(f"Failed to load {parsed_args.file}")
                        logger.error(e)
                        return
            elif ".json" in input_file:
                import json
                with open(input_file, "r") as stream:
                    try:
                        OBdict = json.load(stream)
                    except json.JSONDecodeError as e:
                        logger.error(f"Failed to load {parsed_args.file}")
                        logger.error(e)
                        return
            else:
                logger.error("Filetype not supported. Must be .yaml, .yml, or .json")
                return
            OB = ObservingBlock(OBdict)

    if parsed_args.dry_run:
        logger.info("Dry run:")
        logger.info(f"Function: {mod_str}")
        logger.info(f"Args string: {' '.join(final_args)}")
        logger.info(f"Args dict: {parsed_func_args}")
    else:
        logger.debug(f"Executing {mod_str} {' '.join(final_args)}")
        if script is True:
            function.execute(parsed_func_args, OB=OB)
        else:
            function.execute(parsed_func_args)
