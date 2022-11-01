from time import sleep
from packaging import version
from pathlib import Path
from collections import OrderedDict
import yaml

import ktl

from ddoitranslatormodule.KPFTranslatorFunction import KPFTranslatorFunction
from ..calbench.CalLampPower import CalLampPower
from ..calbench.SetCalSource import SetCalSource
from ..calbench.SetND1 import SetND1
from ..calbench.SetND2 import SetND2
from ..spectrograph.SetExptime import SetExptime
from ..spectrograph.SetSourceSelectShutters import SetSourceSelectShutters
from ..spectrograph.SetTimedShutters import SetTimedShutters
from ..spectrograph.SetTriggeredDetectors import SetTriggeredDetectors
from ..spectrograph.StartExposure import StartExposure
from ..spectrograph.WaitForReady import WaitForReady
from ..spectrograph.WaitForReadout import WaitForReadout
from ..fiu.ConfigureFIU import ConfigureFIU


class RunCalOB(KPFTranslatorFunction):
    '''Script which executes a single calibration OB.
    
    Can be called by `ddoi_script_functions.execute_observation`.
    '''
    @classmethod
    def pre_condition(cls, args, logger, cfg):

        # Use file input for OB instead of args (temporary)
        if args.get('OBfile', None) is not None:
            OBfile = Path(args.get('OBfile')).expanduser()
            if OBfile.exists() is True:
                OB = yaml.safe_load(open(OBfile, 'r'))
                print(f"WARNING: Using OB information from file {OBfile}")
        else:
            raise NotImplementedError('Passing OB as args not implemented')

        # Check template name
        OB_name = OB.get('Template_Name', None)
        if OB_name is None:
            return False
        if OB_name != 'kpf_cal':
            return False
        # Check template version
#         OB_version = OB.get('Template_Version', None)
#         if OB_version is None:
#             return False
#         OB_version = version.parse(f"{OB_version}")
#         compatible_version = version.parse(cfg.get('templates', OB_name))
#         if compatible_version != OB_version:
#             return False
        return True

    @classmethod
    def perform(cls, args, logger, cfg):
        # Use file input for OB instead of args (temporary)
        if args.get('OBfile', None) is not None:
            OBfile = Path(args.get('OBfile')).expanduser()
            if OBfile.exists() is True:
                OB = yaml.safe_load(open(OBfile, 'r'))
                print(f"WARNING: Using OB information from file {OBfile}")
        else:
            raise NotImplementedError('Passing OB as args not implemented')

        # Assumes lamp is on and has warmed up
        print(f"Wait for any existing exposures to be complete")
        WaitForReady.execute({})

        print(f"Configuring FIU")
        ConfigureFIU.execute({'mode': 'Calibration'})

        print(f"Setting source select shutters")
        SetSourceSelectShutters.execute(args)

        print(f"Setting timed shutters")
        SetTimedShutters.execute(args)

        print(f"Set Detector List")
        SetTriggeredDetectors.execute(args)

        for calibration in args.get('SEQ_Calibrations'):
            print(f"Setting cal source: {calibration.get('CalSource')}")
            SetCalSource.execute(calibration)

            print(f"Set ND1 Filter Wheel")
            SetND1.execute(calibration)

            print(f"Set ND2 Filter Wheel")
            SetND2.execute(calibration)

            print(f"Set exposure time")
            SetExptime.execute(calibration)

            nexp = calibration.get('nExp', 1)
            for j in range(nexp):
                print(f"  Starting expoure {j+1}/{nexp}")
                StartExposure.execute({})
                WaitForReadout.execute({})
                print(f"  Readout has begun")
                WaitForReady.execute({})
                print(f"  Readout complete")

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


if __name__ == '__main__':
    description = '''Runs script bypassing the translator command line tools. 
    Uses a YAML input file to get OB contents.
    '''
    p = argparse.ArgumentParser(description=description)
    p.add_argument('OBfile', type=int,
                   help="A yaml file describing the cal OB")
    args = p.parse_args()
    
    calOB = yaml.safe_load(open(args.OBfile, 'r'))
    RunCalOB.execute(OB)

