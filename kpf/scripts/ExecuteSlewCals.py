import os
from time import sleep
from packaging import version
from pathlib import Path

import ktl

from ddoitranslatormodule.KPFTranslatorFunction import KPFTranslatorFunction
from .. import (log, KPFException, FailedPreCondition, FailedPostCondition,
                FailedToReachDestination, check_input)
from . import register_script, obey_scriptrun, check_scriptstop
from ..calbench.CalLampPower import CalLampPower
from ..calbench.SetCalSource import SetCalSource
from ..calbench.SetFlatFieldFiberPos import SetFlatFieldFiberPos
from ..calbench.SetND1 import SetND1
from ..calbench.SetND2 import SetND2
from ..calbench.WaitForCalSource import WaitForCalSource
from ..calbench.WaitForFlatFieldFiberPos import WaitForFlatFieldFiberPos
from ..calbench.WaitForND1 import WaitForND1
from ..calbench.WaitForND2 import WaitForND2
from ..fvc.FVCPower import FVCPower
from ..spectrograph.SetObject import SetObject
from ..spectrograph.SetExptime import SetExptime
from ..spectrograph.SetSourceSelectShutters import SetSourceSelectShutters
from ..spectrograph.SetTimedShutters import SetTimedShutters
from ..spectrograph.SetTriggeredDetectors import SetTriggeredDetectors
from ..spectrograph.StartAgitator import StartAgitator
from ..spectrograph.StartExposure import StartExposure
from ..spectrograph.StopAgitator import StopAgitator
from ..spectrograph.WaitForReady import WaitForReady
from ..spectrograph.WaitForReadout import WaitForReadout
from ..fiu.ConfigureFIU import ConfigureFIU
from ..fiu.WaitForConfigureFIU import WaitForConfigureFIU
from .WaitForLampsWarm import WaitForLampsWarm


class ExecuteSlewCals(KPFTranslatorFunction):
    '''Script which executes the observations of a Slew Cal
    '''
    abortable = True

    def abort_execution(args, logger, cfg):
        scriptstop = ktl.cache('kpfconfig', 'SCRIPTSTOP')
        log.warning('Abort recieved, setting kpfconfig.SCRTIPSTOP=Yes')
        scriptstop.write('Yes')

    @classmethod
    @obey_scriptrun
    def pre_condition(cls, args, logger, cfg):
        check_input(args, 'Template_Name', allowed_values=['kpf_slewcal'])
        check_input(args, 'Template_Version', version_check=True, value_min='0.4')
        return True

    @classmethod
    @register_script(Path(__file__).name, os.getpid())
    def perform(cls, args, logger, cfg):
        log.info('-------------------------')
        log.info(f"Running {cls.__name__}")
        for key in args:
            log.debug(f"  {key}: {args[key]}")
        log.info('-------------------------')

        # Setup
        log.info(f"Wait for any existing exposures to be complete")
        WaitForReady.execute({})
        log.info(f"Configuring FIU")
        ConfigureFIU.execute({'mode': 'Calibration', 'wait': False})
        log.info(f"Set Detector List")
        SetTriggeredDetectors.execute(args)
        log.info(f"Set Source Select Shutters")
        SetSourceSelectShutters.execute({'SSS_Science': True,
                                         'SSS_Sky': True,
                                         'SSS_SoCalSci': False,
                                         'SSS_SoCalCal': False,
                                         'SSS_CalSciSky': True})

        exposestatus = ktl.cache('kpfexpose', 'EXPOSE')

        runagitator = True # <- read KTL keyword when available

        ## ----------------------------------------------------------------
        ## First, configure lamps and cal bench (may happen during readout)
        ## ----------------------------------------------------------------
        calsource = 'EtalonFiber' # <- read KTL keyword when available
        nd1 = args.get('CalND1')
        nd2 = args.get('CalND2')
        log.info(f"Set ND1, ND2 Filter Wheels: {nd1}, {nd2}")
        SetND1.execute({'CalND1': nd1, 'wait': False})
        SetND2.execute({'CalND2': nd2, 'wait': False})
        log.info(f"Waiting for Octagon/CalSource, ND1, ND2, FIU")
        WaitForND1.execute(args)
        WaitForND2.execute(args)
        WaitForCalSource.execute({'CalSource': calsource})
        WaitForConfigureFIU.execute({'mode': 'Calibration'})

        check_scriptstop() # Stop here if requested

        ## ----------------------------------------------------------------
        ## Second, configure kpfexpose (may not happen during readout)
        ## ----------------------------------------------------------------
        # Wait for current exposure to readout
        if exposestatus.read() != 'Ready':
            log.info(f"Waiting for kpfexpose to be Ready")
            WaitForReady.execute({})
            log.info(f"Readout complete")
            sleep(archon_time_shim)
            check_scriptstop() # Stop here if requested
        log.info(f"Set exposure time: {args.get('Exptime'):.3f}")
        SetExptime.execute(args)
        # No need to specify TimedShutter_Scrambler
        args['TimedShutter_Scrambler'] = True
        log.debug(f"Automatically setting TimedShutter_Scrambler: {args['TimedShutter_Scrambler']}")
        # No need to specify TimedShutter_CaHK
        args['TimedShutter_CaHK'] = args['TriggerCaHK']
        log.debug(f"Automatically setting TimedShutter_CaHK: {args['TimedShutter_CaHK']}")
        # No need to specify TimedShutter_FlatField
        args['TimedShutter_FlatField'] = False
        log.debug(f"Automatically setting TimedShutter_FlatField: {args['TimedShutter_FlatField']}")
        log.info(f"Setting timed shutters")
        SetTimedShutters.execute(args)
        log.info(f"Setting OBJECT: {args.get('Object')}")
        SetObject.execute(args)

        ## ----------------------------------------------------------------
        ## Third, take actual exposures
        ## ----------------------------------------------------------------
        nexp = args.get('nExp', 1)
        for j in range(nexp):
            check_scriptstop() # Stop here if requested
            # Wait for current exposure to readout
            if exposestatus.read() != 'Ready':
                log.info(f"Waiting for kpfexpose to be Ready")
                WaitForReady.execute({})
                log.info(f"Readout complete")
                check_scriptstop() # Stop here if requested
            # Start next exposure
            if runagitator is True:
                StartAgitator.execute({})
            log.info(f"Starting expoure {j+1}/{nexp} ({args.get('Object')})")
            StartExposure.execute({})
            WaitForReadout.execute({})
            log.info(f"Readout has begun")
            if runagitator is True:
                StopAgitator.execute({})

    @classmethod
    def post_condition(cls, args, logger, cfg):
        return True
