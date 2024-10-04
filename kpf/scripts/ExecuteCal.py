import os
import traceback
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
from kpf.calbench.IsCalSourceEnabled import IsCalSourceEnabled
from kpf.calbench.SetCalSource import SetCalSource
from kpf.calbench.SetFlatFieldFiberPos import SetFlatFieldFiberPos
from kpf.calbench.SetLFCtoAstroComb import SetLFCtoAstroComb
from kpf.calbench.SetLFCtoStandbyHigh import SetLFCtoStandbyHigh
from kpf.calbench.SetND1 import SetND1
from kpf.calbench.SetND2 import SetND2
from kpf.calbench.TakeIntensityReading import TakeIntensityReading
from kpf.calbench.WaitForCalSource import WaitForCalSource
from kpf.calbench.WaitForFlatFieldFiberPos import WaitForFlatFieldFiberPos
from kpf.calbench.WaitForLampWarm import WaitForLampWarm
from kpf.calbench.WaitForLFCReady import WaitForLFCReady
from kpf.calbench.WaitForND1 import WaitForND1
from kpf.calbench.WaitForND2 import WaitForND2
from kpf.fvc.FVCPower import FVCPower
from kpf.spectrograph.QueryFastReadMode import QueryFastReadMode
from kpf.spectrograph.SetObject import SetObject
from kpf.spectrograph.SetExpTime import SetExpTime
from kpf.spectrograph.SetSourceSelectShutters import SetSourceSelectShutters
from kpf.spectrograph.SetTimedShutters import SetTimedShutters
from kpf.spectrograph.SetTriggeredDetectors import SetTriggeredDetectors
from kpf.spectrograph.StartAgitator import StartAgitator
from kpf.spectrograph.StartExposure import StartExposure
from kpf.spectrograph.StopAgitator import StopAgitator
from kpf.spectrograph.WaitForL0File import WaitForL0File
from kpf.spectrograph.WaitForReady import WaitForReady
from kpf.spectrograph.WaitForReadout import WaitForReadout
from kpf.fiu.ConfigureFIU import ConfigureFIU
from kpf.fiu.WaitForConfigureFIU import WaitForConfigureFIU
from kpf.utils.SetTargetInfo import SetTargetInfo
from kpf.utils.ZeroOutSlewCalTime import ZeroOutSlewCalTime
from kpf.expmeter.SetExpMeterExpTime import SetExpMeterExpTime
from kpf.expmeter.SetupExpMeter import SetupExpMeter
from kpf.utils.SendEmail import SendEmail


class ExecuteCal(KPFTranslatorFunction):
    '''Script which executes a single observation from a Calibration sequence

    This must have arguments as input, either from a file using the `-f` command
    line tool, or passed in from the execution engine.

    ARGS:
    =====
    :calibrations `kpf.ObservingBlocks.Calibration.Calibration` A calibration
                  OB component.
    '''
    @classmethod
    def pre_condition(cls, calibration):
        pass

    @classmethod
    def perform(cls, calibration):
        log.info('-------------------------')
        log.info(f"Running {cls.__name__}")
        for key in calibration:
            log.debug(f"  {key}: {calibration[key]}")
        log.info('-------------------------')
        exposestatus = ktl.cache('kpfexpose', 'EXPOSE')
        kpfconfig = ktl.cache('kpfconfig')
        runagitator = kpfconfig['USEAGITATOR'].read(binary=True)
        fast_read_mode = QueryFastReadMode.execute({})
        # This is a time shim to insert a pause between exposures so that the
        # temperature of the CCDs can be measured by the archons
        archon_time_shim = cfg.getfloat('times', 'archon_temperature_time_shim',
                             fallback=2)

#         log.info(f"Set Detector List")
#         WaitForReady.execute({})
#         SetTriggeredDetectors.execute(OB)



        calsource = calibration.get('CalSource')
        # Skip this lamp if it is not enabled
        if IsCalSourceEnabled.execute({'CalSource': calsource}) == False:
            return
        nd1 = calibration.get('CalND1')
        nd2 = calibration.get('CalND2')
        ## ----------------------------------------------------------------
        ## Configure lamps and cal bench (may happen during readout)
        ## ----------------------------------------------------------------
        check_scriptstop() # Stop here if requested
        ## Setup WideFlat
        if calsource == 'WideFlat':
            log.info('Configuring for WideFlat')
            SetCalSource.execute({'CalSource': 'Home', 'wait': False})
            FF_FiberPos = calibration.get('FF_FiberPos', None)
            SetFlatFieldFiberPos.execute({'FF_FiberPos': FF_FiberPos,
                                          'wait': False})
            SetTargetInfo.execute({})
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
            SetTargetInfo.execute({})
            log.info(f"Waiting for Octagon/CalSource, ND1, ND2, FIU")
            WaitForND1.execute(args)
            WaitForND2.execute(args)
            WaitForCalSource.execute(args)
            WaitForConfigureFIU.execute({'mode': 'Calibration'})
            if calsource == 'LFCFiber':
                ## If we're using the LFC, set it to AstroComb
                ## If that fails, skip this calibration
                try:
                    SetLFCtoAstroComb.execute({})
                except:
                    log.error('Failed to set LFC to AstroComb')
                    try:
                        HB_MENLOSTA = ktl.cache('kpfmon', 'HB_MENLOSTA')
                        LFCREADYSTA = ktl.cache('kpfmon', 'LFCREADYSTA')
                        WOBBLE = ktl.cache('kpfcal', 'WOBBLE')
                        SPECFLAT = ktl.cache('kpfcal', 'SPECFLAT')
                        msg = [f'Failed to set LFC to AstroComb',
                               f'kpfmon.HB_MENLOSTA = {HB_MENLOSTA.read()}',
                               f'kpfmon.LFCREADYSTA = {LFCREADYSTA.read()}',
                               f'kpfcal.WOBBLE = {WOBBLE.read()}',
                               f'kpfcal.SPECFLAT = {SPECFLAT.read()}']
                        SendEmail.execute({'Subject': 'Failed to set LFC to AstroComb',
                                           'Message': '\n'.join(msg)})
                    except Exception as email_err:
                        log.error(f'Sending email failed')
                        log.error(email_err)
                    log.info('Commanding LFC back to Standby High')
                    SetLFCtoStandbyHigh.execute({})
                    return
            # Take intensity monitor reading
            if calsource != 'LFCFiber' and args.get('nointensemon', False) == False:
                WaitForLampWarm.execute(args)
                TakeIntensityReading.execute({})
        ## Setup SoCal
        elif calsource in ['SoCal-CalFib']:
            SetCalSource.execute({'CalSource': calsource, 'wait': False})
            # Open SoCalCal Shutter
            args['SSS_SoCalCal'] = True
            # Set target info
            SetTargetInfo.execute({'TargetName': 'Sun',
                                   'GaiaID': '',
                                   '2MASSID': '',
                                   'Gmag': '-26.9',
                                   'Jmag': '-27.9',
                                   'Teff': '5772',
                                   })
        elif calsource in ['SoCal-SciSky']:
            # Set octagon to simulcal source
            simulcalsource = kpfconfig['SIMULCALSOURCE'].read()
            log.info(f"Setting cal source: {simulcalsource}")
            SetCalSource.execute({'CalSource': simulcalsource, 'wait': False})
            log.info(f"Set ND1, ND2 Filter Wheels: {nd1}, {nd2}")
            SetND1.execute({'CalND1': nd1, 'wait': False})
            SetND2.execute({'CalND2': nd2, 'wait': False})
            log.info(f"Waiting for Octagon/CalSource, ND1, ND2, FIU")
            WaitForND1.execute(args)
            WaitForND2.execute(args)
            WaitForCalSource.execute({'CalSource': simulcalsource})
            WaitForConfigureFIU.execute({'mode': 'Calibration'})
            # Open SoCalSci Shutter
            args['SSS_SoCalSci'] = True
            # Set target info
            SetTargetInfo.execute({'TargetName': 'Sun',
                                   'GaiaID': '',
                                   '2MASSID': '',
                                   'Gmag': '-26.9',
                                   'Jmag': '-27.9',
                                   'Teff': '5772',
                                   })
        # WTF!?
        else:
            raise KPFException(f"CalSource {calsource} not recognized")

        ## ----------------------------------------------------------------
        ## Configure exposure meter
        ## ----------------------------------------------------------------
        args = SetupExpMeter.execute(args)
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
            check_scriptstop() # Stop here if requested
        SetTriggeredDetectors.execute(args)
        log.info(f"Set exposure time: {args.get('ExpTime'):.3f}")
        SetExpTime.execute(args)
        log.info(f"Setting source select shutters")
        # No need to specify SSS_CalSciSky in OB/calibration
        if calsource in ['SoCal-SciSky']:
            args['SSS_CalSciSky'] = False
        elif calsource in ['SoCal-CalFib']:
            args['SSS_CalSciSky'] = True
        else:
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
        nexp = int(args.get('nExp', 1))
        exptime = float(args.get('ExpTime'))
        # If we are in fast read mode, turn on agitator once
        if runagitator and fast_read_mode:
            StartAgitator.execute({})
        # Loop over exposures
        for j in range(nexp):
            check_scriptstop() # Stop here if requested
            # Wait for current exposure to readout
            if exposestatus.read() != 'Ready':
                log.info(f"Waiting for kpfexpose to be Ready")
                WaitForReady.execute({})
                log.info(f"Readout complete")
                if exptime < 2:
                    log.debug(f'Sleep {archon_time_shim:.1f}s for temperature reading')
                    sleep(archon_time_shim)
                check_scriptstop() # Stop here if requested
            # Check LFC if it is the source
            if calsource == 'LFCFiber':
                LFCready = WaitForLFCReady.execute({})
                if LFCready is False:
                    log.error('LFC is not ready, skipping remaining LFC frames')
                    SetLFCtoStandbyHigh.execute({})
                    return
            # Start agitator for each exposure if we are in normal read mode
            if runagitator and not fast_read_mode:
                StartAgitator.execute({})
            # Start next exposure
            log.info(f"Starting expoure {j+1}/{nexp} ({args.get('Object')})")
            StartExposure.execute({})
            if exptime > 10:
                WaitForL0File.execute({})
            WaitForReadout.execute({})
            log.info(f"Readout has begun")
            # Stop agitator after each exposure if we are in normal read mode
            if runagitator and not fast_read_mode:
                StopAgitator.execute({})
            if calsource in ['LFCFiber', 'EtalonFiber']:
                ZeroOutSlewCalTime.execute({})
        # If we are in fast read mode, turn off agitator at end
        if runagitator and fast_read_mode:
            StopAgitator.execute({})
        ## If we used WideFlat, set FF_FiberPos back to blank at end
        if calsource == 'WideFlat':
            SetFlatFieldFiberPos.execute({'FF_FiberPos': 'Blank'})
        ## If we're using the LFC, set it back to StandbyHigh
        if calsource == 'LFCFiber' and args.get('leave_lamps_on', False) is False:
            SetLFCtoStandbyHigh.execute({})

    @classmethod
    def post_condition(cls, calibration):
        pass
