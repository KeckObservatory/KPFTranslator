import os
import traceback
from time import sleep
from packaging import version
from pathlib import Path

import ktl

from kpf import log, cfg
from kpf.exceptions import *
from kpf.KPFTranslatorFunction import KPFFunction, KPFScript
from kpf.scripts import (register_script, obey_scriptrun, check_scriptstop,
                         add_script_log)
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
from kpf.fiu.WaitForConfigureFIU import WaitForConfigureFIU
from kpf.scripts.SetTargetInfo import SetTargetInfo
from kpf.utils.ZeroOutSlewCalTime import ZeroOutSlewCalTime
from kpf.expmeter.SetExpMeterExpTime import SetExpMeterExpTime
from kpf.utils.SendEmail import SendEmail
from kpf.spectrograph.SetProgram import SetProgram


class ExecuteCal(KPFFunction):
    '''Script which executes a single observation from a Calibration sequence

    Args:
        calibration (dict): A calibration OB component in dictionary format (e.g.
                            using the output of the `.to_dict()` method of a
                            `kpf.ObservingBlocks.Calibration.Calibration` instance).

    KTL Keywords Used:

    - `kpfexpose.EXPOSE`
    - `kpfconfig.USEAGITATOR`
    - `kpfconfig.SIMULCALSOURCE`
    - `kpfconfig.SCRIPTMSG`
    - `kpfmon.HB_MENLOSTA`
    - `kpfmon.LFCREADYSTA`
    - `kpfcal.WOBBLE`
    - `kpfcal.SPECFLATIR`

    Functions Called:

    - `kpf.calbench.IsCalSourceEnabled`
    - `kpf.calbench.SetCalSource`
    - `kpf.calbench.SetFlatFieldFiberPos`
    - `kpf.calbench.SetLFCtoAstroComb`
    - `kpf.calbench.SetLFCtoStandbyHigh`
    - `kpf.calbench.SetND1`
    - `kpf.calbench.SetND2`
    - `kpf.calbench.TakeIntensityReading`
    - `kpf.calbench.WaitForCalSource`
    - `kpf.calbench.WaitForFlatFieldFiberPos`
    - `kpf.calbench.WaitForLampWarm`
    - `kpf.calbench.WaitForLFCReady`
    - `kpf.calbench.WaitForND1`
    - `kpf.calbench.WaitForND2`
    - `kpf.spectrograph.QueryFastReadMode`
    - `kpf.spectrograph.SetObject`
    - `kpf.spectrograph.SetExpTime`
    - `kpf.spectrograph.SetSourceSelectShutters`
    - `kpf.spectrograph.SetTimedShutters`
    - `kpf.spectrograph.SetTriggeredDetectors`
    - `kpf.spectrograph.StartAgitator`
    - `kpf.spectrograph.StartExposure`
    - `kpf.spectrograph.StopAgitator`
    - `kpf.spectrograph.WaitForL0File`
    - `kpf.spectrograph.WaitForReady`
    - `kpf.spectrograph.WaitForReadout`
    - `kpf.fiu.WaitForConfigureFIU`
    - `kpf.scripts.SetTargetInfo`
    - `kpf.utils.ZeroOutSlewCalTime`
    - `kpf.expmeter.SetExpMeterExpTime`
    - `kpf.utils.SendEmail`
    - `kpf.spectrograph.SetProgram`
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

        calsource = calibration.get('CalSource')
        # Skip this lamp if it is not enabled
        if IsCalSourceEnabled.execute({'CalSource': calsource}) == False:
            return


        ## ----------------------------------------------------------------
        ## Configure lamps and cal bench (may happen during readout)
        ## ----------------------------------------------------------------
        check_scriptstop() # Stop here if requested
        ## Setup WideFlat
        if calsource.lower() == 'dark':
            log.info('Configuring for Dark')
            SetCalSource.execute({'CalSource': 'Home', 'wait': False})
            SetFlatFieldFiberPos.execute({'FF_FiberPos': 'Blank', 'wait': False})
            SetTargetInfo.execute({})
            log.info(f"Waiting for Octagon/CalSource, FF_FiberPos, FIU")
            WaitForCalSource.execute({'CalSource': 'Home'})
            WaitForFlatFieldFiberPos.execute({'FF_FiberPos': 'Blank'})
        elif calsource == 'WideFlat':
            log.info('Configuring for WideFlat')
            SetCalSource.execute({'CalSource': 'Home', 'wait': False})
            FF_FiberPos = calibration.get('FF_FiberPos', None)
            SetFlatFieldFiberPos.execute({'FF_FiberPos': FF_FiberPos,
                                          'wait': False})
            SetTargetInfo.execute({})
            log.info(f"Waiting for Octagon/CalSource, FF_FiberPos, FIU")
            WaitForCalSource.execute({'CalSource': 'Home'})
            WaitForFlatFieldFiberPos.execute(calibration)
        ## Setup Octagon Lamps and LFCFiber
        elif calsource in ['BrdbandFiber', 'U_gold', 'U_daily', 'Th_daily',
                           'Th_gold', 'LFCFiber', 'EtalonFiber']:
            log.info(f"Setting cal source: {calsource}")
            SetCalSource.execute({'CalSource': calsource, 'wait': False})
            nd1 = calibration.get('CalND1')
            nd2 = calibration.get('CalND2')
            log.info(f"Set ND1, ND2 Filter Wheels: {nd1}, {nd2}")
            SetND1.execute({'CalND1': nd1, 'wait': False})
            SetND2.execute({'CalND2': nd2, 'wait': False})
            SetTargetInfo.execute({})
            log.info(f"Waiting for Octagon/CalSource, ND1, ND2, FIU")
            WaitForND1.execute(calibration)
            WaitForND2.execute(calibration)
            WaitForCalSource.execute(calibration)
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
                        SPECFLATVIS = ktl.cache('kpfcal', 'SPECFLATVIS')
                        SPECFLATIR = ktl.cache('kpfcal', 'SPECFLATIR')
                        msg = [f'Failed to set LFC to AstroComb',
                               f'kpfmon.HB_MENLOSTA = {HB_MENLOSTA.read()}',
                               f'kpfmon.LFCREADYSTA = {LFCREADYSTA.read()}',
                               f'kpfcal.WOBBLE = {WOBBLE.read()}',
                               f'kpfcal.SPECFLATVIS = {SPECFLATVIS.read()}',
                               f'kpfcal.SPECFLATIR = {SPECFLATIR.read()}']
                        SendEmail.execute({'Subject': 'Failed to set LFC to AstroComb',
                                           'Message': '\n'.join(msg)})
                    except Exception as email_err:
                        log.error(f'Sending email failed')
                        log.error(email_err)
                    log.info('Commanding LFC back to Standby High')
                    SetLFCtoStandbyHigh.execute({})
                    return
            # Take intensity monitor reading
            if calsource != 'LFCFiber' and calibration.get('IntensityMonitor', False):
                WaitForLampWarm.execute(calibration)
                TakeIntensityReading.execute({})
        ## Setup SoCal
        elif calsource in ['SoCal-CalFib']:
            SetCalSource.execute({'CalSource': calsource, 'wait': False})
            # Open SoCalCal Shutter
            calibration['OpenSoCalCalShutter'] = True
            nd1 = calibration.get('CalND1')
            nd2 = calibration.get('CalND2')
            log.info(f"Set ND1, ND2 Filter Wheels: {nd1}, {nd2}")
            SetND1.execute({'CalND1': nd1, 'wait': False})
            SetND2.execute({'CalND2': nd2, 'wait': False})
            log.info(f"Waiting for Octagon/CalSource, ND1, ND2, FIU")
            WaitForND1.execute(calibration)
            WaitForND2.execute(calibration)
            WaitForCalSource.execute({'CalSource': calibration})
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
            nd1 = calibration.get('CalND1')
            nd2 = calibration.get('CalND2')
            log.info(f"Set ND1, ND2 Filter Wheels: {nd1}, {nd2}")
            SetND1.execute({'CalND1': nd1, 'wait': False})
            SetND2.execute({'CalND2': nd2, 'wait': False})
            log.info(f"Waiting for Octagon/CalSource, ND1, ND2, FIU")
            WaitForND1.execute(calibration)
            WaitForND2.execute(calibration)
            WaitForCalSource.execute({'CalSource': simulcalsource})
            # Open SoCalSci Shutter
            calibration['OpenSoCalSciShutter'] = True
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
        if calibration.get('ExpMeterMode', 'off') == 'control':
            SetExpMeterTerminationParameters.execute(calibration)
        if calibration.get('AutoExpMeter', False) == True:
            log.warning('AutoExpMeter is not supported for calibrations')
        if calibration.get('ExpMeterExpTime', None) is not None:
            log.debug(f"Setting ExpMeterExpTime = {calibration['ExpMeterExpTime']:.1f}")
            SetExpMeterExpTime.execute(calibration)


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
        # Set program ID to ENG
        SetProgram.execute({'progname': 'ENG'})
        # Triggered Detectors
        calibration['TriggerExpMeter'] = calibration.get('ExpMeterMode', 'off') in ['monitor', 'control']
        log.info(f"Set Detector List")
        SetTriggeredDetectors.execute(calibration)
        # Source Select Shutters
        if calsource.lower() == 'dark':
            SetSourceSelectShutters.execute({})
        else:
            if calsource in ['SoCal-SciSky']:
                calibration['OpenCalSciSkyShutter'] = False
            elif calsource in ['SoCal-CalFib']:
                calibration['OpenCalSciSkyShutter'] = True
            else:
                calibration['OpenCalSciSkyShutter'] = calibration['OpenScienceShutter'] or calibration['OpenSkyShutter']
            SetSourceSelectShutters.execute(calibration)
        # Timed Shutters
        calibration['TimedShutter_CaHK'] = calibration.get('TriggerCaHK', False) and calsource.lower() != 'dark'
        calibration['TimedShutter_Scrambler'] = (calibration.get('TriggerGreen', False) or calibration.get('TriggerRed', False)) and calsource.lower() != 'dark'
        calibration['TimedShutter_SimulCal'] = calibration.get('TakeSimulCal', False) and calsource.lower() != 'dark'
        calibration['TimedShutter_FlatField'] = (calibration.get('WideFlatPos', 'Blank') != 'Blank') and calsource.lower() != 'dark'
        log.info(f"Setting timed shutters")
        SetTimedShutters.execute(calibration)

        log.info(f"Setting OBJECT: {calibration.get('Object')}")
        SetObject.execute(calibration)

        log.info(f"Set exposure time: {calibration.get('ExpTime'):.3f}")
        SetExpTime.execute(calibration)

        WaitForConfigureFIU.execute({'mode': 'Calibration'})
        WaitForLampWarm.execute(calibration)

        ## ----------------------------------------------------------------
        ## Take actual exposures
        ## ----------------------------------------------------------------
        nexp = int(calibration.get('nExp', 1))
        exptime = float(calibration.get('ExpTime'))
        # If we are in fast read mode, turn on agitator once
        if runagitator and fast_read_mode and calsource.lower() != 'dark':
            StartAgitator.execute({})
        # Loop over exposures
        for j in range(nexp):
            check_scriptstop() # Stop here if requested
            # Wait for current exposure to readout
            if exposestatus.read() != 'Ready':
                log.info(f"Waiting for kpfexpose to be Ready")
                WaitForReady.execute({})
                log.info(f"Readout complete")
                check_scriptstop() # Stop here if requested
            # Check LFC if it is the source
            if calsource == 'LFCFiber':
                LFCready = WaitForLFCReady.execute({})
                if LFCready is False:
                    log.error('LFC is not ready, skipping remaining LFC frames')
                    SetLFCtoStandbyHigh.execute({})
                    return
            # Start agitator for each exposure if we are in normal read mode
            if runagitator and not fast_read_mode and calsource.lower() != 'dark':
                StartAgitator.execute({})
            # Set triggered detectors. This is here to force a check of the
            # ENABLED status for each detector.
            SetTriggeredDetectors.execute(calibration)
            # Start next exposure
            exptime = float(calibration.get('ExpTime'))
            msg = f"Exposing {j+1}/{nexp} ({exptime:.0f} s)"
            kpfconfig['SCRIPTMSG'].write(msg)
            log.info(msg+ f" ({calibration.get('Object')})")
            StartExposure.execute({})
            if exptime > 10:
                WaitForL0File.execute({})
            WaitForReadout.execute({})
            msg = f"Reading out {j+1}/{nexp}"
            kpfconfig['SCRIPTMSG'].write(msg)
            log.info(msg)
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
        if calsource == 'LFCFiber' and calibration.get('leave_lamps_on', False) is False:
            SetLFCtoStandbyHigh.execute({})
        SetObject.execute({'Object': ''})

    @classmethod
    def post_condition(cls, calibration):
        pass
