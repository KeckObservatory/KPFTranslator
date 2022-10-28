from time import sleep

import ktl

from ddoitranslatormodule.KPFTranslatorFunction import KPFTranslatorFunction
from . import RunCalOB


class RunCalSequence(KPFTranslatorFunction):
    '''Script which loops over a set of input calibration OB yaml files and
    executes each calibration OB in turn.
    '''
    @classmethod
    def pre_condition(cls, args, logger, cfg):
        return True

    @classmethod
    def perform(cls, args, logger, cfg):
        sequences = [yaml.load(open(file)) for file in args.files]
        print(f"Read {len(sequences)} sequence files")

        lamps = set([entry['OctagonSource'] for entry in sequences])
        for lamp in lamps:
            # Turn on lamps
            PowerOnCalSource.execute({'cal_source': lamp})

        warm_up_time = max([entry['WarmUp'] for entry in sequences])

        print(f"Sleeping {warm_up_time:.0f} s for lamps to warm up")
        sleep(warm_up_time)

        for count in range(0,args.count):
            for i,sequence in enumerate(sequences):
                print(f"(Repeat {count+1}/{args.count}): Executing sequence "
                         f"{i+1}/{len(sequences)} ({args.files[i]})")

                # Set Cal Source
                SetCalSource.execute({'cal_source': sequence.get('OctagonSource')})

                # Set Source Select Shutters
                SetSourceSelectShutters.execute({})

                # Set Timed Shutters
                SetTimedShutters.execute({})

                # Set ND1 Filter Wheel
                SetND1.execute({})

                # Set ND2 Filter Wheel
                SetND2.execute({}})

                # Set exposure time
                SetExptime.execute({}})

                # Wait for Exposure to be Complete
                WaitForReady.execute()

                # Set Detector List
                SetTriggeredDetectors.execute({})

                nexp = sequence.get('nExp', 1)
                for j in range(nexp):
                    # Wait for Exposure to be Complete
                    WaitForReady.execute()

                    print(f"  Starting expoure {j+1}/{nexp}")
                    if args.noexp is False: StartExposure.execute()

                    # Wait for Readout to Begin
                    if args.noexp is False: WaitForReadout.execute()

        if args.lampsoff is True:
            for lamp in lamps:
                # Turn off lamps
                PowerOffCalSource.execute({'lamp': lamp})

        # Wait for Exposure to be Complete
        WaitForReady.execute()

    @classmethod
    def post_condition(cls, args, logger, cfg):
        return True
