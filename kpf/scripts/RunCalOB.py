from time import sleep
from packaging import version
from pathlib import Path
from collections import OrderedDict
import yaml

import ktl

from ddoitranslatormodule.KPFTranslatorFunction import KPFTranslatorFunction
from .. import log
from ..calbench.CalLampPower import CalLampPower
from ..calbench.SetCalSource import SetCalSource
from ..calbench.SetND1 import SetND1
from ..calbench.SetND2 import SetND2
from ..calbench.WaitForCalSource import WaitForCalSource
from ..calbench.WaitForND1 import WaitForND1
from ..calbench.WaitForND2 import WaitForND2
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
                log.warning(f"Using OB information from file {OBfile}")
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
                log.warning(f"Using OB information from file {OBfile}")
        else:
            raise NotImplementedError('Passing OB as args not implemented')

        # Assumes lamp is on and has warmed up
        log.info(f"Wait for any existing exposures to be complete")
        WaitForReady.execute({})

        log.info(f"Configuring FIU")
        ConfigureFIU.execute({'mode': 'Calibration'})

        log.info(f"Setting source select shutters")
        SetSourceSelectShutters.execute(OB)

        log.info(f"Setting timed shutters")
        SetTimedShutters.execute(OB)

        log.info(f"Set Detector List")
        SetTriggeredDetectors.execute(OB)

        for calibration in OB.get('SEQ_Calibrations'):
            log.info(f"Setting cal source: {calibration.get('CalSource')}")
            SetCalSource.execute({'CalSource': calibration.get('CalSource'),
                                  'wait': False})

            log.info(f"Set ND1 Filter Wheel: {calibration.get('CalND1')}")
            SetND1.execute({'CalND1': calibration.get('CalND1'),
                            'wait': False})

            log.info(f"Set ND2 Filter Wheel: {calibration.get('CalND2')}")
            SetND2.execute({'CalND2': calibration.get('CalND2'),
                            'wait': False})

            log.info(f"Set exposure time: {calibration.get('ExpTime'):.3f}")
            SetExptime.execute(calibration)

            log.info(f"Waiting for ND1")
            WaitForND1(calibration)
            log.info(f"Waiting for ND2")
            WaitForND2(calibration)
            log.info(f"Waiting for Octagon (CalSource)")
            WaitForCalSource(calibration)

            nexp = calibration.get('nExp', 1)
            for j in range(nexp):
                log.info(f"  Starting expoure {j+1}/{nexp}")
                StartExposure.execute({})
                WaitForReadout.execute({})
                log.info(f"  Readout has begun")
                WaitForReady.execute({})
                log.info(f"  Readout complete")

    @classmethod
    def post_condition(cls, args, logger, cfg):
        kpfexpose = ktl.cache('kpfexpose')
        expose = kpfexpose['EXPOSE']
        status = expose.read()
        if status != 'Ready':
            msg = f"Final detector state mismatch: {status} != Ready"
            log.error(msg)
            return False
        return True

    @classmethod
    def add_cmdline_args(cls, parser, cfg=None):
        """
        The arguments to add to the command line interface.
        """
        args_to_add = OrderedDict()
        args_to_add['OBfile'] = {'type': str,
                                 'help': ('A YAML fortmatted file with the OB '
                                          'to be executed. Will override OB '
                                          'data delivered as args.')}
        parser = cls._add_args(parser, args_to_add, print_only=False)
        return super().add_cmdline_args(parser, cfg)
