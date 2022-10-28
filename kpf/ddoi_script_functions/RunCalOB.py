from time import sleep
from packaging import version

import ktl

from ddoitranslatormodule.KPFTranslatorFunction import KPFTranslatorFunction
from ..calbench import lamp_has_warmed_up
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


class RunCalOB(KPFTranslatorFunction):
    '''Script which executes a single calibration OB.
    
    Can be called by `ddoi_script_functions.execute_observation`.
    '''
    @classmethod
    def pre_condition(cls, args, logger, cfg):
        OB_name = args.get('Template_Name', None)
        OB_version = args.get('Template_Version', None)
        if OB_name is None:
            return False
        if OB_version is None
            return False
        OB_version = version.parse(OB_version)
        cfg = cls._load_config(cls, cfg)
        compatible_version = version.parse(cfg.get('templates', OB_name))
        if compatible_version != OB_version:
            return False
        return lamp_has_warmed_up(args.get('CalSource'))

    @classmethod
    def perform(cls, args, logger, cfg):
        # Assumes lamp is on and has warmed up
        print(f"Wait for any existing exposures to be complete")
        WaitForReady.execute({})

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

