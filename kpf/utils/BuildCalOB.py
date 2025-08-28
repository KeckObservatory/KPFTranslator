from pathlib import Path
import copy

from kpf.exceptions import *
from kpf.KPFTranslatorFunction import KPFFunction, KPFScript
from kpf.ObservingBlocks.ObservingBlock import ObservingBlock
from kpf.scripts.EstimateOBDuration import EstimateOBDuration


##-------------------------------------------------------------------------
## BuildCalOB
##-------------------------------------------------------------------------
class BuildCalOB(KPFFunction):
    '''From a set of standard prescriptions, build the described calibration OB.

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

        if args.get('save', '') != '':
            OB.write_to(args.get('save'), overwrite=args.get('overwrite', False))

        if args.get('estimate', False):
            duration = EstimateOBDuration.execute({'verbose': True}, OB=OB)

        return OB

    @classmethod
    def post_condition(cls, argsKPFFunction):
        pass

    @classmethod
    def add_cmdline_args(cls, parser):
        parser.add_argument('calinputs', nargs='*',
                            help="Calibrations to take in the form ")
        parser.add_argument("-t", "--time", "--estimate", dest="estimate",
                            default=False, action="store_true",
                            help="Estimate the execution time for this OB?")
        parser.add_argument("-s", "--save", dest="save", type=str, default='',
                            help="Save resulting OB to the specified file.")
        parser.add_argument("-o", "--overwrite", dest="overwrite",
                            default=False, action="store_true",
                            help="Overwrite output file if it exists?")
        return super().add_cmdline_args(parser)
