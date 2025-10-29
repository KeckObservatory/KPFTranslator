from pathlib import Path
import copy

from kpf.exceptions import *
from kpf.KPFTranslatorFunction import KPFFunction, KPFScript
from kpf.ObservingBlocks.ObservingBlock import ObservingBlock
from kpf.scripts.EstimateOBDuration import EstimateOBDuration
from kpf.scripts.RunOB import RunOB


##-------------------------------------------------------------------------
## BuildCalOB
##-------------------------------------------------------------------------
class BuildCalOB(KPFFunction):
    '''From a set of standard prescriptions, build the described calibration OB.
    Given a list of input strings, parse them in to variations of the standard
    calibrations and create an OB for them.

    The input string format is `[CalSource],[Object],[nExp],[keywords]`. The
    first 3 entries are required while the keywords section is optional. Any
    unspecified values default to match the same CalSource entry in the example
    OB file in this repo at `kpf/ObservingBlocks/exampleOBs/Calibration.yaml`.

    For example, and input of `EtalonFiber,slewcal,5` will generate an OB which
    takes 5 etalon frames with the object name of "slewcal". No keywords are
    provided, so all other elements of the OB are the default values (e.g. the
    exposure time and ND filters).

    The keywords can be used to modify those default values in the OB. For
    example, if the input is:
    `[CalSource],[Object],[nExp],[keywords],IntensityMonitor=True`
    then the resulting OB will have the `IntensityMonitor` value set to True
    rather than the default of False and
    `[CalSource],[Object],[nExp],[keywords],ExpTime=30`
    will result in an OB with 30 second exposure times instead of the default
    of 40 seconds.

    Multiple inputs can be given to create multi-calibration OBs, either as a
    list in python or on the command line. For example:
    `kpfdo BuildCalOB Dark,autocal-dark,1,ExpTime=1200 EtalonFiber,autocal-etalon-all-midday,3,IntensityMonitor=True BrdbandFiber,autocal-flat-all,95,IntensityMonitor=True`
    will generate an OB with three calibrations: a 1200 second dark, 3 Etalon
    frames, and 95 flat field frames.

    Args:
        calinputs (list of strings): Input strings as described above.
        estimate (bool): Generate the OB, run the `EstimateOBDuration` tool,
                         and print the results to screen.
        save (string): Save resulting OB to the specified file.
        overwrite (bool): Overwrite output file if it exists?
        execute (bool): Execute the resulting OB?

    Functions Called:

    - `EstimateOBDuration`
    - `RunOB`
    '''
    @classmethod
    def pre_condition(cls, args):
        pass

    @classmethod
    def perform(cls, args):
        # Build dict of example calibrations
        example_cal_file = Path(__file__).parent.parent / 'ObservingBlocks' / 'exampleOBs' / 'Calibrations.yaml'
        if example_cal_file.exists() != True:
            print(f'Failed to open {example_cal_file:s}')
            return
        example_OB = ObservingBlock(example_cal_file)
        example_cals = {}
        for cal in example_OB.Calibrations:
            if cal.CalSource not in example_cals.keys():
                example_cals[str(cal.CalSource)] = cal

        # Build fresh OB
        OB = ObservingBlock({})
        for calinput in args.get('calinputs'):
            calspec = calinput.split(',')
            # [CalSource],[Object],[nExp],**kwargs
            example = example_cals.get(calspec[0], None)
            if example is None:
                print(f'Unable to find example calibrations for {calspec[0]}')
            else:
                cal = copy.deepcopy(example)
                cal.set('Object', calspec[1])
                cal.set('nExp', int(calspec[2]))
                if len(calspec) > 3:
                    kwargs = calspec[3:]
                    for kwarg in kwargs:
                        key,value = kwarg.split('=')
                        if key in ['Exptime']:
                            cal.set(key, float(value))
                        elif key in ['TriggerCaHK', 'TriggerGreen', 'TriggerRed',
                                     'IntensityMonitor', 'OpenScienceShutter',
                                     'OpenSkyShutter', 'TakeSimulCal']:
                            cal.set(key, bool(value))
                        else:
                            cal.set(key, value)
                OB.Calibrations.append(cal)

        if args.get('save', '') not in ['', None]:
            OB.write_to(args.get('save'), overwrite=args.get('overwrite', False))

        if args.get('estimate', False) or args.get('execute', False):
            cal_strings = [str(cal) for cal in OB.Calibrations]
            cal_string = ','.join(cal_strings)
            print(f"# {cal_string}")
            duration = EstimateOBDuration.execute({'verbose': True}, OB=OB)
        if args.get('execute', False):
            RunOB.execute({}, OB=OB)

        return OB

    @classmethod
    def post_condition(cls, args):
        pass

    @classmethod
    def add_cmdline_args(cls, parser):
        parser.add_argument('calinputs', nargs='*',
                            help="Calibrations to take in the form ")
        parser.add_argument("-v", "-t", "--time", "--estimate", dest="estimate",
                            default=False, action="store_true",
                            help="Estimate the execution time for this OB?")
        parser.add_argument("-s", "--save", dest="save", type=str, default='',
                            help="Save resulting OB to the specified file.")
        parser.add_argument("-o", "--overwrite", dest="overwrite",
                            default=False, action="store_true",
                            help="Overwrite output file if it exists?")
        parser.add_argument("--execute", dest="execute",
                            default=False, action="store_true",
                            help="Execute the resulting OB?")
        return super().add_cmdline_args(parser)
