from time import sleep

import ktl
from ddoitranslatormodule.BaseFunction import TranslatorModuleFunction
from ddoitranslatormodule.DDOIExceptions import *

from ..utils import *


class RunCalSequence(TranslatorModuleFunction):
    '''Loops over all input files (args.files). Each file is parsed as YAML
    and the keyword-value pairs in the resulting dictionary control the
    subsequent actions.
    
    The loop is repeated a number of times equal to the args.count value (which
    is the -n argument on the command line).

    This function still needs work to adapt it from the original KPFtools format
    to the proper DSI Translator format.
    '''
    def __init__(self):
        super().__init__()

    @classmethod
    def pre_condition(cls, args, logger, cfg):
        for file in args.files:
            file = Path(file)
            if file.exists() is False:
                msg = f"Input file {args.file} does not exist"
                print(msg)
                return False

    @classmethod
    def perform(cls, args, logger, cfg):
        sequences = [yaml.load(open(file)) for file in args.files]
        print(f"Read {len(sequences)} sequence files")

        lamps = set([entry['OctagonSource'] for entry in sequences])
        for lamp in lamps:
            # Turn on lamps
            action = PowerOnCalSource()
            action.execute({'lamp': lamp})

        warm_up_time = max([entry['WarmUp'] for entry in sequences])

        print(f"Sleeping {warm_up_time:.0f} s for lamps to warm up")
        sleep(warm_up_time)

        for count in range(0,args.count):
            for i,sequence in enumerate(sequences):
                print(f"(Repeat {count+1}/{args.count}): Executing sequence "
                         f"{i+1}/{len(sequences)} ({args.files[i]})")

                # Set Cal Source
                action = SetCalSource()
                action.execute(sequence)

                # Set Source Select Shutters
                action = SetSourceSelectShutters()
                action.execute(sequence)

                # Set Timed Shutters
                action = SetTimedShutters()
                action.execute(sequence)

                # Set ND1 Filter Wheel
                action = SetND1()
                action.execute(sequence)

                # Set ND2 Filter Wheel
                action = SetND2()
                action.execute(sequence)

                # Set exposure time
                action = SetExptime()
                action.execute(sequence)

                # Wait for Exposure to be Complete
                action = WaitForReady()
                action.execute(sequence)

                # Set Detector List
                action = SetTriggeredDetectors()
                action.execute(sequence)

                nexp = sequence.get('nExp', 1)
                for j in range(nexp):
                    # Wait for Exposure to be Complete
                    action = WaitForReady()
                    action.execute(sequence)

                    log.info(f"  Starting expoure {j+1}/{nexp}")
                    # Start Exposure
                    action = StartExposure()
                    if args.noexp is False: action.execute(sequence)

                    # Wait for Readout to Begin
                    action = WaitForReadout()
                    if args.noexp is False: action.execute(sequence)


        if args.lampsoff is True:
            for lamp in lamps:
                # Turn off lamps
                action = PowerOffCalSource()
                action.execute({'lamp': lamp})

        # Wait for Exposure to be Complete
        action = WaitForReady()
        action.execute(sequence)

    @classmethod
    def post_condition(cls, args, logger, cfg):
        kpfexpose = ktl.cache('kpfexpose')
        expose = kpfexpose['EXPOSE']
        status = expose.read()
        if status != 'Ready':
            msg = f"Final detector state mismatch: {status} != Ready"
            print(msg)
            return False
        return True
