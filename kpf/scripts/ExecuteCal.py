import os
from time import sleep
from packaging import version
from pathlib import Path

import ktl

from kpf.KPFTranslatorFunction import KPFTranslatorFunction
from .. import (log, KPFException, FailedPreCondition, FailedPostCondition,
                FailedToReachDestination, check_input)
from . import register_script, obey_scriptrun, check_scriptstop, add_script_log
from ..calbench.CalLampPower import CalLampPower
from ..calbench.SetCalSource import SetCalSource
from ..calbench.SetFlatFieldFiberPos import SetFlatFieldFiberPos
from ..calbench.SetND1 import SetND1
from ..calbench.SetND2 import SetND2
from ..calbench.TakeIntensityReading import TakeIntensityReading
from ..calbench.WaitForCalSource import WaitForCalSource
from ..calbench.WaitForFlatFieldFiberPos import WaitForFlatFieldFiberPos
from ..calbench.WaitForLampWarm import WaitForLampWarm
from ..calbench.WaitForND1 import WaitForND1
from ..calbench.WaitForND2 import WaitForND2
from ..fvc.FVCPower import FVCPower
from ..spectrograph.SetObject import SetObject
from ..spectrograph.SetExptime import SetExptime
from ..spectrograph.SetSourceSelectShutters import SetSourceSelectShutters
from ..spectrograph.SetTimedShutters import SetTimedShutters
from ..spectrograph.StartAgitator import StartAgitator
from ..spectrograph.StartExposure import StartExposure
from ..spectrograph.StopAgitator import StopAgitator
from ..spectrograph.WaitForReady import WaitForReady
from ..spectrograph.WaitForReadout import WaitForReadout
from ..fiu.ConfigureFIU import ConfigureFIU
from ..fiu.WaitForConfigureFIU import WaitForConfigureFIU


class ExecuteCal(KPFTranslatorFunction):
    '''Script which executes a single observation from a Calibration sequence
    
    Can be called by `ddoi_script_functions.execute_observation`.
    '''
    abortable = True

    @classmethod
    def abort_execution(args, logger, cfg):
        scriptstop = ktl.cache('kpfconfig', 'SCRIPTSTOP')
        log.warning('Abort recieved, setting kpfconfig.SCRTIPSTOP=Yes')
        scriptstop.write('Yes')

    @classmethod
    def pre_condition(cls, args, logger, cfg):
        check_input(args, 'Template_Name', allowed_values=['kpf_lamp'])
        check_input(args, 'Template_Version', version_check=True, value_min='0.5')
        return True

    @classmethod
    def perform(cls, args, logger, cfg):
        exposestatus = ktl.cache('kpfexpose', 'EXPOSE')
        kpfconfig = ktl.cache('kpfconfig')
        runagitator = kpfconfig['USEAGITATOR'].read(binary=True)
        # This is a time shim to insert a pause between exposures so that the
        # temperature of the CCDs can be measured by the archons
        archon_time_shim = cfg.get('times', 'archon_temperature_time_shim',
                             fallback=2)

        calsource = args.get('CalSource')
        nd1 = args.get('CalND1')
        nd2 = args.get('CalND2')
        ## ----------------------------------------------------------------
        ## First, configure lamps and cal bench (may happen during readout)
        ## ----------------------------------------------------------------
        check_scriptstop() # Stop here if requested
        ## Setup WideFlat
        if calsource == 'WideFlat':
            log.info('Configuring for WideFlat')
            SetCalSource.execute({'CalSource': 'Home', 'wait': False})
            FF_FiberPos = args.get('FF_FiberPos', None)
            SetFlatFieldFiberPos.execute({'FF_FiberPos': FF_FiberPos,
                                          'wait': False})
            log.info(f"Waiting for Octagon/CalSource, FF_FiberPos, FIU")
            WaitForCalSource.execute({'CalSource': 'Home'})
            WaitForFlatFieldFiberPos.execute(args)
            WaitForConfigureFIU.execute({'mode': 'Calibration'})
        ## Setup Octagon Lamps and LFCFiber
        elif calsource in ['BrdbandFiber', 'U_gold', 'U_daily', 'Th_daily',
                           'Th_gold', 'LFCFiber', 'EtalonFiber']:
            log.info(f"Setting cal source: {calsource}")
            SetCalSource.execute({'CalSource': calsource, 'wait': False})
            log.info(f"Set ND1, ND2 Filter Wheels: {nd1}, {nd2}")
            SetND1.execute({'CalND1': nd1, 'wait': False})
            SetND2.execute({'CalND2': nd2, 'wait': False})
            log.info(f"Waiting for Octagon/CalSource, ND1, ND2, FIU")
            WaitForND1.execute(args)
            WaitForND2.execute(args)
            WaitForCalSource.execute(args)
            WaitForConfigureFIU.execute({'mode': 'Calibration'})
            # Take intensity monitor reading
            TakeIntensityReading.execute({})
        ## Setup SoCal
        elif calsource in ['SoCal-CalFib']:
            raise NotImplementedError()
        # WTF!?
        else:
            msg = f"CalSource {calsource} not recognized"
            log.error(msg)
            raise Exception(msg)

        ## ----------------------------------------------------------------
        ## Second, configure kpfexpose (may not happen during readout)
        ## ----------------------------------------------------------------
        check_scriptstop() # Stop here if requested
        # Wait for current exposure to readout
        if exposestatus.read() != 'Ready':
            log.info(f"Waiting for kpfexpose to be Ready")
            WaitForReady.execute({})
            log.info(f"Readout complete")
            sleep(archon_time_shim)
            check_scriptstop() # Stop here if requested
        log.info(f"Set exposure time: {args.get('Exptime'):.3f}")
        SetExptime.execute(args)
        log.info(f"Setting source select shutters")
        # No need to specify SSS_CalSciSky in OB/calibration
        args['SSS_CalSciSky'] = args['SSS_Science'] or args['SSS_Sky']
        log.debug(f"Automatically setting SSS_CalSciSky: {args['SSS_CalSciSky']}")
        SetSourceSelectShutters.execute(args)

        # No need to specify TimedShutter_Scrambler in OB/calibration
        args['TimedShutter_Scrambler'] = args['SSS_Science'] or args['SSS_Sky']
        log.debug(f"Automatically setting TimedShutter_Scrambler: {args['TimedShutter_Scrambler']}")
        # No need to specify TimedShutter_FlatField in OB/calibration
        args['TimedShutter_FlatField'] = (args['CalSource'] == 'WideFlat')
        log.debug(f"Automatically setting TimedShutter_FlatField: {args['TimedShutter_FlatField']}")
        # Set TimedShutter_SimulCal
        args['TimedShutter_SimulCal'] = args['TakeSimulCal']
        log.debug(f"Automatically setting TimedShutter_SimulCal: {args['TakeSimulCal']}")
        log.info(f"Setting timed shutters")
        SetTimedShutters.execute(args)
        log.info(f"Setting OBJECT: {args.get('Object')}")
        SetObject.execute(args)

        ## ----------------------------------------------------------------
        ## Third, take actual exposures
        ## ----------------------------------------------------------------
        WaitForLampWarm.execute(args)
        nexp = args.get('nExp', 1)
        for j in range(nexp):
            check_scriptstop() # Stop here if requested
            # Wait for current exposure to readout
            if exposestatus.read() != 'Ready':
                log.info(f"Waiting for kpfexpose to be Ready")
                WaitForReady.execute({})
                log.info(f"Readout complete")
                sleep(archon_time_shim)
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
        if calsource == 'WideFlat':
            SetFlatFieldFiberPos.execute({'FF_FiberPos': 'Blank'})

    @classmethod
    def post_condition(cls, args, logger, cfg):
        return True
