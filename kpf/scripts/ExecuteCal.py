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
from kpf.calbench.CalLampPower import CalLampPower
from kpf.calbench.SetCalSource import SetCalSource
from kpf.calbench.SetFlatFieldFiberPos import SetFlatFieldFiberPos
from kpf.calbench.SetND1 import SetND1
from kpf.calbench.SetND2 import SetND2
from kpf.calbench.TakeIntensityReading import TakeIntensityReading
from kpf.calbench.WaitForCalSource import WaitForCalSource
from kpf.calbench.WaitForFlatFieldFiberPos import WaitForFlatFieldFiberPos
from kpf.calbench.WaitForLampWarm import WaitForLampWarm
from kpf.calbench.WaitForND1 import WaitForND1
from kpf.calbench.WaitForND2 import WaitForND2
from kpf.fvc.FVCPower import FVCPower
from kpf.spectrograph.SetObject import SetObject
from kpf.spectrograph.SetExpTime import SetExpTime
from kpf.spectrograph.SetSourceSelectShutters import SetSourceSelectShutters
from kpf.spectrograph.SetTimedShutters import SetTimedShutters
from kpf.spectrograph.StartAgitator import StartAgitator
from kpf.spectrograph.StartExposure import StartExposure
from kpf.spectrograph.StopAgitator import StopAgitator
from kpf.spectrograph.WaitForReady import WaitForReady
from kpf.spectrograph.WaitForReadout import WaitForReadout
from kpf.fiu.ConfigureFIU import ConfigureFIU
from kpf.fiu.WaitForConfigureFIU import WaitForConfigureFIU
from kpf.utils.ZeroOutSlewCalTime import ZeroOutSlewCalTime
from kpf.expmeter.SetExpMeterExpTime import SetExpMeterExpTime


class ExecuteCal(KPFTranslatorFunction):
    '''Script which executes a single observation from a Calibration sequence

    This must have arguments as input, either from a file using the `-f` command
    line tool, or passed in from the execution engine.

    Can be called by `ddoi_script_functions.execute_observation`.

    ARGS:
    =====
    None
    '''
    abortable = True

    @classmethod
    def pre_condition(cls, args, logger, cfg):
        check_input(args, 'Template_Name', allowed_values=['kpf_lamp'])
        check_input(args, 'Template_Version', version_check=True, value_min='0.5')

    @classmethod
    def perform(cls, args, logger, cfg):
        exposestatus = ktl.cache('kpfexpose', 'EXPOSE')
        kpfconfig = ktl.cache('kpfconfig')
        runagitator = kpfconfig['USEAGITATOR'].read(binary=True)
        # This is a time shim to insert a pause between exposures so that the
        # temperature of the CCDs can be measured by the archons
        archon_time_shim = cfg.getfloat('times', 'archon_temperature_time_shim',
                             fallback=2)

        calsource = args.get('CalSource')
        nd1 = args.get('CalND1')
        nd2 = args.get('CalND2')
        ## ----------------------------------------------------------------
        ## Configure lamps and cal bench (may happen during readout)
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
            if calsource != 'LFCFiber':
                WaitForLampWarm.execute(args)
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
        ## Configure exposure meter
        ## ----------------------------------------------------------------
        if args.get('AutoExpMeter', False) == True:
            raise KPFException('AutoExpMeter is not supported for calibrations')
        if args.get('ExpMeterExpTime', None) is not None:
            log.debug(f"Setting ExpMeterExpTime = {args['ExpMeterExpTime']:.1f}")
            SetExpMeterExpTime.execute(args)

        ## ----------------------------------------------------------------
        ## Configure kpfexpose (may not happen during readout)
        ## ----------------------------------------------------------------
        check_scriptstop() # Stop here if requested
        # Wait for current exposure to readout
        if exposestatus.read() != 'Ready':
            log.info(f"Waiting for kpfexpose to be Ready")
            WaitForReady.execute({})
            log.info(f"Readout complete")
            sleep(archon_time_shim)
            check_scriptstop() # Stop here if requested
        log.info(f"Set exposure time: {args.get('ExpTime'):.3f}")
        SetExpTime.execute(args)
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
        args['TimedShutter_SimulCal'] = args.get('TakeSimulCal', False)
        log.debug(f"Automatically setting TimedShutter_SimulCal: {args['TakeSimulCal']}")
        log.info(f"Setting timed shutters")
        SetTimedShutters.execute(args)
        log.info(f"Setting OBJECT: {args.get('Object')}")
        SetObject.execute(args)

        ## ----------------------------------------------------------------
        ## Take actual exposures
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
            if calsource in ['LFCFiber', 'EtalonFiber']:
                ZeroOutSlewCalTime.execute({})
        if calsource == 'WideFlat':
            SetFlatFieldFiberPos.execute({'FF_FiberPos': 'Blank'})

    @classmethod
    def post_condition(cls, args, logger, cfg):
        pass
