import os
from time import sleep
from packaging import version
from pathlib import Path
import yaml

import ktl

from ddoitranslatormodule.KPFTranslatorFunction import KPFTranslatorFunction
from .. import (log, KPFException, FailedPreCondition, FailedPostCondition,
                FailedToReachDestination, check_input)
from . import register_script, clear_script, check_script_stop
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


class RunCalOB(KPFTranslatorFunction):
    '''Script which executes a single calibration OB.
    
    Can be called by `ddoi_script_functions.execute_observation`.
    '''
    @classmethod
    def pre_condition(cls, args, logger, cfg):
        # Use file input for OB instead of args (temporary)
        check_input(args, 'OBfile')
        OBfile = Path(args.get('OBfile')).expanduser()
        if OBfile.exists() is True:
            OB = yaml.safe_load(open(OBfile, 'r'))
            log.warning(f"Using OB information from file {OBfile}")
        check_input(OB, 'Template_Name', allowed_values=['kpf_cal'])
        check_input(OB, 'Template_Version', allowed_values=['0.4'])
        return True

    @classmethod
    def perform(cls, args, logger, cfg):
        # Register this script with kpfconfig
        register_script(__file__, os.getpid())
        # Use file input for OB instead of args (temporary)
        OBfile = Path(args.get('OBfile')).expanduser()
        OB = yaml.safe_load(open(OBfile, 'r'))

        log.info('-------------------------')
        log.info(f"Running RunCalOB")
        for key in OB:
            if key not in ['SEQ_Darks', 'SEQ_Calibrations']:
                log.debug(f"  {key}: {OB[key]}")
            else:
                log.debug(f"  {key}:")
                for entry in OB[key]:
                    log.debug(f"    {entry}")
        log.info('-------------------------')

        # Setup
        log.info(f"Wait for any existing exposures to be complete")
        WaitForReady.execute({})
        log.info(f"Configuring FIU")
        ConfigureFIU.execute({'mode': 'Calibration', 'wait': False})
        log.info(f"Set Detector List")
        SetTriggeredDetectors.execute(OB)
        log.info(f"Ensuring back illumination LEDs are off")
        CalLampPower.execute({'lamp': 'ExpMeterLED', 'power': 'off'})
        CalLampPower.execute({'lamp': 'CaHKLED', 'power': 'off'})
        CalLampPower.execute({'lamp': 'SciLED', 'power': 'off'})
        CalLampPower.execute({'lamp': 'SkyLED', 'power': 'off'})

        exposestatus = ktl.cache('kpfexpose', 'EXPOSE')

        # This is a time shim to insert a pause between exposures so that the
        # temperature of the CCDs can be measured by the archons
        archon_time_shim = cfg.get('times', 'archon_temperature_time_shim',
                             fallback=2)

        # First Do the darks and biases
        darks = OB.get('SEQ_Darks', [])
        if len(darks) > 0:
            log.info(f"Setting source select shutters")
            SetSourceSelectShutters.execute({}) # No args defaults all to false
            log.info(f"Setting timed shutters")
            SetTimedShutters.execute({}) # No args defaults all to false
            log.info(f"Setting OCTAGON to Home position")
            SetCalSource.execute({'CalSource': 'Home'})
            log.info(f"Setting FlatField Fiber position to 'Blank'")
            SetFlatFieldFiberPos.execute({'FF_FiberPos': 'Blank'})
        for dark in darks:
            # Wait for current exposure to readout
            if exposestatus.read() != 'Ready':
                log.info(f"Waiting for kpfexpose to be Ready")
                WaitForReady.execute({})
                log.info(f"Readout complete")
                sleep(archon_time_shim)
            check_script_stop() # Stop here if requested
            log.info(f"Setting OBJECT: {dark.get('Object')}")
            SetObject.execute(dark)
            log.info(f"Set exposure time: {dark.get('Exptime'):.3f}")
            SetExptime.execute(dark)
            nexp = dark.get('nExp', 1)
            for j in range(nexp):
                check_script_stop() # Stop here if requested
                # Wait for current exposure to readout
                if exposestatus.read() != 'Ready':
                    log.info(f"Waiting for kpfexpose to be Ready")
                    WaitForReady.execute({})
                    log.info(f"Readout complete")
                    sleep(archon_time_shim)
                    check_script_stop() # Stop here if requested
                # Start next exposure
                log.info(f"Starting exposure {j+1}/{nexp} ({dark.get('Object')})")
                StartExposure.execute({})
                WaitForReadout.execute({})
                log.info(f"Readout has begun")

        # Wait for lamps to finish warming up
#         WaitForLampsWarm.execute(OB)

        # Run lamp calibrations
        runagitator = OB.get('RunAgitator', False)
        for calibration in OB.get('SEQ_Calibrations'):
            calsource = calibration.get('CalSource')
            nd1 = calibration.get('CalND1')
            nd2 = calibration.get('CalND2')
            ## ----------------------------------------------------------------
            ## First, configure lamps and cal bench (may happen during readout)
            ## ----------------------------------------------------------------
            check_script_stop() # Stop here if requested
            ## Setup WideFlat
            if calsource == 'WideFlat':
                log.info('Configuring for WideFlat')
                SetCalSource.execute({'CalSource': 'Home', 'wait': False})
                FF_FiberPos = calibration.get('FF_FiberPos', None)
                SetFlatFieldFiberPos.execute({'FF_FiberPos': FF_FiberPos,
                                              'wait': False})
                log.info(f"Waiting for Octagon/CalSource, FF_FiberPos, FIU")
                WaitForCalSource.execute({'CalSource': 'Home'})
                WaitForFlatFieldFiberPos.execute(calibration)
                WaitForConfigureFIU.execute({'mode': 'Calibration'})
            ## Setup Octagon Lamps and LFCFiber
            elif calsource in ['BrdbandFiber', 'U_gold', 'U_daily', 'Th_daily',
                               'Th_gold', 'LFCFiber']:
                log.info(f"Setting cal source: {calsource}")
                SetCalSource.execute({'CalSource': calsource, 'wait': False})
                log.info(f"Set ND1, ND2 Filter Wheels: {nd1}, {nd2}")
                SetND1.execute({'CalND1': nd1, 'wait': False})
                SetND2.execute({'CalND2': nd2, 'wait': False})
                log.info(f"Waiting for Octagon/CalSource, ND1, ND2, FIU")
                WaitForND1.execute(calibration)
                WaitForND2.execute(calibration)
                WaitForCalSource.execute(calibration)
                WaitForConfigureFIU.execute({'mode': 'Calibration'})
            ## Setup Etalon
            elif calsource in ['EtalonFiber']:
                raise NotImplementedError()
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
            check_script_stop() # Stop here if requested
            # Wait for current exposure to readout
            if exposestatus.read() != 'Ready':
                log.info(f"Waiting for kpfexpose to be Ready")
                WaitForReady.execute({})
                log.info(f"Readout complete")
                sleep(archon_time_shim)
                check_script_stop() # Stop here if requested
            log.info(f"Set exposure time: {calibration.get('Exptime'):.3f}")
            SetExptime.execute(calibration)
            log.info(f"Setting source select shutters")
            # No need to specify SSS_CalSciSky in OB/calibration
            calibration['SSS_CalSciSky'] = calibration['SSS_Science'] or calibration['SSS_Sky']
            log.debug(f"Automatically setting SSS_CalSciSky: {calibration['SSS_CalSciSky']}")
            # No need to specify TimedShutter_Scrambler in OB/calibration
            calibration['TimedShutter_Scrambler'] = calibration['SSS_Science'] or calibration['SSS_Sky']
            log.debug(f"Automatically setting TimedShutter_Scrambler: {calibration['TimedShutter_Scrambler']}")
            # No need to specify TimedShutter_CaHK in OB/calibration
            calibration['TimedShutter_CaHK'] = OB['TriggerCaHK']
            log.debug(f"Automatically setting TimedShutter_CaHK: {calibration['TimedShutter_CaHK']}")
            # No need to specify TimedShutter_FlatField in OB/calibration
            calibration['TimedShutter_FlatField'] = (calibration['CalSource'] == 'WideFlat')
            log.debug(f"Automatically setting TimedShutter_FlatField: {calibration['TimedShutter_FlatField']}")
            SetSourceSelectShutters.execute(calibration)
            log.info(f"Setting timed shutters")
            SetTimedShutters.execute(calibration)
            log.info(f"Setting OBJECT: {calibration.get('Object')}")
            SetObject.execute(calibration)

            ## ----------------------------------------------------------------
            ## Third, take actual exposures
            ## ----------------------------------------------------------------
            nexp = calibration.get('nExp', 1)
            for j in range(nexp):
                check_script_stop() # Stop here if requested
                # Wait for current exposure to readout
                if exposestatus.read() != 'Ready':
                    log.info(f"Waiting for kpfexpose to be Ready")
                    WaitForReady.execute({})
                    log.info(f"Readout complete")
                    sleep(archon_time_shim)
                    check_script_stop() # Stop here if requested
                # Start next exposure
                if runagitator is True:
                    StartAgitator.execute({})
                log.info(f"Starting expoure {j+1}/{nexp} ({calibration.get('Object')})")
                StartExposure.execute({})
                if runagitator is True:
                    StopAgitator.execute({})
                WaitForReadout.execute({})
                log.info(f"Readout has begun")
            if calsource == 'WideFlat':
                SetFlatFieldFiberPos.execute({'FF_FiberPos': 'Blank'})

        # Register end of this script with kpfconfig
        clear_script()

    @classmethod
    def post_condition(cls, args, logger, cfg):
        timeout = cfg.get('times', 'kpfexpose_timeout', fallback=0.01)
        expr = f"($kpfexpose.EXPOSE == Ready)"
        success = ktl.waitFor(expr, timeout=timeout)
        return success

    @classmethod
    def add_cmdline_args(cls, parser, cfg=None):
        '''The arguments to add to the command line interface.
        '''
        from collections import OrderedDict
        args_to_add = OrderedDict()
        args_to_add['OBfile'] = {'type': str,
                                 'help': ('A YAML fortmatted file with the OB '
                                          'to be executed. Will override OB '
                                          'data delivered as args.')}
        parser = cls._add_args(parser, args_to_add, print_only=False)
        return super().add_cmdline_args(parser, cfg)
