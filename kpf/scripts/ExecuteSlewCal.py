import os
from time import sleep
from packaging import version
from pathlib import Path

import ktl

from kpf.KPFTranslatorFunction import KPFTranslatorFunction
from kpf import (log, KPFException, FailedPreCondition, FailedPostCondition,
                 FailedToReachDestination, check_input)
from kpf.scripts import (register_script, obey_scriptrun, check_scriptstop,
                         add_script_log)
from kpf.calbench.IsCalSourceEnabled import IsCalSourceEnabled
from kpf.calbench.SetND1 import SetND1
from kpf.calbench.SetND2 import SetND2
from kpf.calbench.WaitForCalSource import WaitForCalSource
from kpf.calbench.WaitForND1 import WaitForND1
from kpf.calbench.WaitForND2 import WaitForND2
from kpf.spectrograph.SetObject import SetObject
from kpf.spectrograph.SetExpTime import SetExpTime
from kpf.spectrograph.SetSourceSelectShutters import SetSourceSelectShutters
from kpf.spectrograph.SetTimedShutters import SetTimedShutters
from kpf.spectrograph.SetTriggeredDetectors import SetTriggeredDetectors
from kpf.spectrograph.StartAgitator import StartAgitator
from kpf.spectrograph.StartExposure import StartExposure
from kpf.spectrograph.StopAgitator import StopAgitator
from kpf.spectrograph.WaitForReady import WaitForReady
from kpf.spectrograph.WaitForReadout import WaitForReadout
from kpf.fiu.ConfigureFIU import ConfigureFIU
from kpf.fiu.WaitForConfigureFIU import WaitForConfigureFIU
from kpf.utils.ZeroOutSlewCalTime import ZeroOutSlewCalTime
from kpf.utils.SetTargetInfo import SetTargetInfo


class ExecuteSlewCal(KPFTranslatorFunction):
    '''Script which executes the observations of a Slew Cal

    This must have arguments as input, either from a file using the `-f` command
    line tool, or passed in from the execution engine.

    ARGS:
    =====
    None
    '''
    abortable = True

    @classmethod
    def pre_condition(cls, args, logger, cfg):
        check_input(args, 'Template_Name', allowed_values=['kpf_slewcal'])
        check_input(args, 'Template_Version', version_check=True, value_min='0.4')

    @classmethod
    def perform(cls, args, logger, cfg):
        log.info('-------------------------')
        log.info(f"Running {cls.__name__}")
        for key in args:
            log.debug(f"  {key}: {args[key]}")
        log.info('-------------------------')

        kpfconfig = ktl.cache('kpfconfig')
        calsource = kpfconfig['SIMULCALSOURCE'].read()
        runagitator = kpfconfig['USEAGITATOR'].read(binary=True)

        # Skip this lamp if it is not enabled
        if IsCalSourceEnabled.execute({'CalSource': calsource}) == False:
            return

        ## ----------------------------------------------------------------
        ## First, configure lamps and cal bench (may happen during readout)
        ## ----------------------------------------------------------------
        log.info(f"Configuring FIU")
        ConfigureFIU.execute({'mode': 'Calibration', 'wait': False})

        check_scriptstop() # Stop here if requested

        # Configure Cal Bench
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
        exposestatus = ktl.cache('kpfexpose', 'EXPOSE')
        if exposestatus.read() != 'Ready':
            log.info(f"Waiting for kpfexpose to be Ready")
            WaitForReady.execute({})
            log.info(f"Readout complete")
            check_scriptstop() # Stop here if requested
        log.info(f"Set Detector List")
        SetTriggeredDetectors.execute(args)
        log.info(f"Set Source Select Shutters")
        SetSourceSelectShutters.execute({'SSS_Science': True,
                                         'SSS_Sky': True,
                                         'SSS_SoCalSci': False,
                                         'SSS_SoCalCal': False,
                                         'SSS_CalSciSky': True})
        log.info(f"Set exposure time: {args.get('ExpTime'):.3f}")
        SetExpTime.execute(args)
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
        log.info(f"Clearing stellar parameters")
        target_info = {'TargetName': '', 'GaiaID': '', '2MASSID': '',
                       'Parallax': 0, 'RadialVelocity': 0,
                       'Gmag': '', 'Jmag': '', 'Teff': 45000}
        SetTargetInfo.execute(target_info)

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
            ZeroOutSlewCalTime.execute({})

    @classmethod
    def post_condition(cls, args, logger, cfg):
        pass
