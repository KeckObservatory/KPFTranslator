import importlib
import traceback
import sys
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
        raw =  configparser.ConfigParser()
        raw.read(filename)
        self.cfg = raw
        self.prefix = raw['common']['prefix']
        self.suffix = raw['common']['suffix']
    
    def get_entry_points(self) -> List[str]:
        eps = [key for key in self.cfg['links']]
        return eps
    
    def print_entry_points(self, prefix=""):
        for i in self.get_entry_points():
            print(prefix + i)

    def get_link(self, entry_point):
        output = ""
        if self.prefix:
            output += self.prefix + "."
        output += self.cfg['links'][entry_point]
        if self.suffix:
            output += "." + self.suffix
        return output

def get_linked_function(linking_tbl, key):
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
        import it

    Raises
    ------
    DDOITranslatorModuleNotFoundException
        If there is not an associated Translator Module
    """

    # Check to see if there is an entry matching the given key
    if key not in linking_tbl.get_entry_points():
        raise DDOITranslatorModuleNotFoundException(f"Unable to find an import for {key}")
    module_str = linking_tbl.get_link(key)
    
    try:
        # Try to import the package from the string in the linking table
        mod = importlib.import_module(module_str)
        
        # For each non-builtin property in the module, check if:
        #   - It is an Inherited function (e.g. base function)
        #   - There is a perform method. This assumes nothing else will have a
        #     method called perform, which may be an unsafe assumption
        # If those conditions are met, we found our module, and return it and
        # its path
        for property in [i for i in dir(mod) if not i.startswith("__")]:
            if "ModuleFunction" not in property:
                if "perform" in dir(getattr(mod, property)):
                    return getattr(mod, property), f"{module_str}.{property}"

        print("Failed to find a class with a perform method")
        return None, None
    except ImportError as e:
        print(f"Failed to import {module_str}")
        print(traceback.format_exc())
        return None, None

def main():

    table_loc = Path(__file__).parent / "linking_table.ini"
    if not table_loc.exists():
        print(f"Failed to find a linking table at {str(table_loc)}")
        print("Exiting...")
        return
    linking_tbl = LinkingTable(table_loc)

    #
    ### Handle command line arguments
    #

    args = sys.argv
    dry_run = False
    # Help:
    if '-h' in args or '--help' in args:
        # If this is help for a specific module:
        if len(args) > 2:
            try:
                function, mod_str = get_linked_function(linking_tbl, args[1])
                print(function.__doc__)
                # parser = ArgumentParser()
                # parser = function.add_cmdline_args(parser)
                # parser.print_help()
                return
            except DDOITranslatorModuleNotFoundException as e:
                print(e)
                print("Available options are:")
                linking_tbl.print_entry_points("   ")
                return
        # Print help for using this CLI script
        else:
            print(f"This is the CLI entry script for {__package__}")
            print(
"""
Options are:
    -l, --list:
        Print all entry points available for use
    -n, --dry-run:
        Print what command would be invoked without actually executing it
""")
            return
    # List:
    if '-l' in args or '--list' in args:
        linking_tbl.print_entry_points()
        return
    # Dry run:
    if '-n' in args or '--dry-run' in args:
        dry_run = True
        if "-n" in args: args.remove("-n")
        if "--dry-run" in args: args.remove("--dry-run")

    #
    ### Handle Execution
    #
    
    try:
        function, mod_str = get_linked_function(linking_tbl, args[1])
        
        parser = ArgumentParser()
        # Call the add cmd line args
        parser = function.add_cmdline_args(parser)

        # Parse the args
        parsed_args = parser.parse_args(args[2:])
        
        if dry_run:
            print(f"Function: {mod_str}\nArgs: [{' '.join(args[2:])}]")
        else:
            print(f"Executing {mod_str} {' '.join(args[2:])}")
            function.execute(parsed_args)
    except DDOITranslatorModuleNotFoundException as e:
        print(e)
    except ImportError as e:
        print(e)
    except TypeError as e:
        print(traceback.format_exc())
if __name__ == "__main__":
    main()
