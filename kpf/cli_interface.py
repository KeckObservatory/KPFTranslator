from email.policy import default
import importlib
import traceback
import sys
import yaml
import configparser
from pathlib import Path
from argparse import ArgumentParser
from typing import Dict, List, Tuple

from ddoitranslatormodule.ddoiexceptions.DDOIExceptions import DDOITranslatorModuleNotFoundException
from ddoitranslatormodule.BaseFunction import TranslatorModuleFunction

class LinkingTable():
    """Class storing the contents of a linking table
    """

    def __init__(self, filename):
        """Create the LinkingTable

        Parameters
        ----------
        filename : str
            Filepath to the linking table
        """
        try:
            with open(filename) as f:
                self.cfg = yaml.load(f, Loader=yaml.FullLoader)
        except:
            print(f"Unable to load {filename}")
            return

        self.prefix = self.cfg['common']['prefix']
        self.suffix = self.cfg['common']['suffix']
        self.links = self.cfg['links']
    
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

    def get_link_and_args(self, entry_point) -> Tuple[str, list]:
        """Gets both an import string for an entry point, and a list of Tuples 
        containing information about default arguments needed

        Parameters
        ----------
        entry_point : str
            Key in the links section in the linking table being searched for

        Returns
        -------
        Tuple[str, list]
            Import string for the entry point, and a list of tuples where the first
            item is the argument that must be inserted, and the second is the index
            where it should go
        """
        link = self.get_link(entry_point)
        args = None
        # Load the config file, and create an array with [None, SADSASD, None, etc...]
        # maybe return a function that takes in a partial arguments array and outputs a full array?
        args = []
        if 'args' in self.links[entry_point].keys():
            for arg in self.links[entry_point]['args']:
                arg_index = arg.split("_")[1]
                args.append((int(arg_index), self.links[entry_point]['args'][arg]))
                # Loop over these tuples and insert them into the execution args
                # i.e. args.insert(idx = tup[0], arg=tup[1])
        return link, args

def get_linked_function(linking_tbl, key) -> Tuple[TranslatorModuleFunction, str]:
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

    Raises
    ------
    DDOITranslatorModuleNotFoundException
        If there is not an associated Translator Module
    """

    # Check to see if there is an entry matching the given key
    if key not in linking_tbl.get_entry_points():
        raise DDOITranslatorModuleNotFoundException(f"Unable to find an import for {key}")
    link, default_args = linking_tbl.get_link_and_args(key)

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
            return getattr(mod, class_str), default_args, link
        except:
            print("Failed to find a class with a perform method")
            return None, None, None

    except ImportError as e:
        print(f"Failed to import {module_str}")
        print(traceback.format_exc())
        return None, None, None

def main():

    #
    ### Build the linking table
    #

    table_loc = Path(__file__).parent / "linking_table.yml"
    if not table_loc.exists():
        print(f"Failed to find a linking table at {str(table_loc)}")
        print("Exiting...")
        return
    linking_tbl = LinkingTable(table_loc)

    #
    ### Handle command line arguments
    #
    
    parser = ArgumentParser(add_help=False)
    parser.add_argument("-l", "--list", dest="list", action="store_true", help="List functions in this module")
    parser.add_argument("-n", "--dry-run", dest="dry_run", action="store_true", help="Print what function would be called with what arguments, with no actual invocation")
    parser.add_argument("-h", "--help", dest="help", action="store_true")
    parser.add_argument("-v", "--verbose", dest="verbose", action="store_true", help="Print extra information")
    parser.add_argument("function_args", nargs="*", help="Function to be executed, and any needed arguments")
    parsed_args = parser.parse_args()
    
    # Help:
    if parsed_args.help:
        # If this is help for a specific module:
        if len(parsed_args.function_args):
            try:
                function, preset_args, mod_str = get_linked_function(linking_tbl, parsed_args.function_args[0])
                func_parser = ArgumentParser()
                func_parser = function.add_cmdline_args(func_parser)
                func_parser.print_help()
                if parsed_args.verbose:
                    print(function.__doc__)
                print(preset_args)
                # figure out how to access the argparse from outside, and print the -h
            except DDOITranslatorModuleNotFoundException as e:
                print(e)
                print("Available options are:")
                linking_tbl.print_entry_points("   ")
        # Print help for using this CLI script
        else:
            parser.print_help()
        return
    # List:
    if parsed_args.list:
        linking_tbl.print_entry_points()
        return


    #
    ### Handle Execution
    #
    
    try:

        # Get the function
        function, args, mod_str = get_linked_function(linking_tbl, parsed_args.function_args[0])
        
        # Insert required default arguments
        final_args = parsed_args.function_args[1:]
        for arg_tup in args:
            final_args.insert(arg_tup[0], str(arg_tup[1]))
        
        # Build an ArgumentParser and attach the function's arguments
        parser = ArgumentParser(add_help=False)
        parser = function.add_cmdline_args(parser)
        parsed_func_args = parser.parse_args(final_args)
        
        
        
        if parsed_args.dry_run:
            print(f"Function: {mod_str}\nArgs: {' '.join(final_args)}")
        else:
            if parsed_args.verbose:
                print(f"Executing {mod_str} {' '.join(final_args)}")
            function.execute(parsed_func_args)

    except DDOITranslatorModuleNotFoundException as e:
        print(e)
    except ImportError as e:
        print(e)
    except TypeError as e:
        print(traceback.format_exc())

if __name__ == "__main__":
    main()
