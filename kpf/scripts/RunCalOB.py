from time import sleep
from packaging import version
from pathlib import Path
import yaml

import ktl

from ddoitranslatormodule.KPFTranslatorFunction import KPFTranslatorFunction
from .. import log
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
from ..spectrograph.StartExposure import StartExposure
from ..spectrograph.WaitForReady import WaitForReady
from ..spectrograph.WaitForReadout import WaitForReadout
from ..fiu.ConfigureFIU import ConfigureFIU
from ..fiu.WaitForConfigureFIU import WaitForConfigureFIU
from ..scripts.SetOutdirs import SetOutdirs
from .WaitForLampsWarm import WaitForLampsWarm


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

        # Setup
        log.info(f"Wait for any existing exposures to be complete")
        WaitForReady.execute({})
        log.info(f"Set OUTDIRs")
        SetOutdirs.execute({})
        log.info(f"Configuring FIU")
        ConfigureFIU.execute({'mode': 'Calibration', 'wait': False})
        log.info(f"Set Detector List")
        SetTriggeredDetectors.execute(OB)
        log.info(f"Ensuring back illumination LEDs are off")
        CalLampPower.execute({'lamp': 'ExpMeterLED', 'power': 'off'})
        CalLampPower.execute({'lamp': 'CaHKLED', 'power': 'off'})
        CalLampPower.execute({'lamp': 'SciLED', 'power': 'off'})
        CalLampPower.execute({'lamp': 'SkyLED', 'power': 'off'})
        log.info(f"Ensuring Cal FVC is off")
        FVCPower.execute({'camera': 'CAL', 'power': 'off'})

        log.info(f"Setting source select shutters")
        SetSourceSelectShutters.execute({}) # No args defaults all to false
        log.info(f"Setting timed shutters")
        SetTimedShutters.execute({}) # No args defaults all to false

        WaitForConfigureFIU.execute({'mode': 'Calibration'})

        # First Do the darks and biases
        darks = OB.get('SEQ_Darks', [])
        if len(darks) > 0:
            log.info(f"Setting OCTAGON to Home position")
            SetCalSource.execute({'CalSource': 'Home'})
            log.info(f"Ensuring FlatField Fiber position is 'Blank'")
            SetFlatFieldFiberPos.execute({'FF_FiberPos': 'Blank'})
        for dark in farks:
            log.info(f"Setting OBJECT: {dark.get('Object')}")
            SetObject.execute(dark)
            log.info(f"Set exposure time: {dark.get('Exptime'):.3f}")
            SetExptime.execute(dark)
            nexp = dark.get('nExp', 1)
            for j in range(nexp):
                log.info(f"  Starting expoure {j+1}/{nexp}")
                StartExposure.execute({})
                WaitForReadout.execute({})
                log.info(f"  Readout has begun")
                WaitForReady.execute({})
                log.info(f"  Readout complete")

        # Wait for lamps to finish warming up
#         WaitForLampsWarm.execute(OB)

        # Run lamp calibrations
        for calibration in OB.get('SEQ_Calibrations'):
            calsource = calibration.get('CalSource')
            log.info(f"Set exposure time: {calibration.get('Exptime'):.3f}")
            SetExptime.execute(calibration)
            log.info(f"Setting source select shutters")
            SetSourceSelectShutters.execute(calibration)
            log.info(f"Setting timed shutters")
            SetTimedShutters.execute(calibration)
            log.info(f"Setting OBJECT: {calibration.get('Object')}")
            SetObject.execute(calibration)
            nexp = calibration.get('nExp', 1)

            ## Setup WideFlat
            if calsource == 'WideFlat':
                log.info('Configuring for WideFlat')
                SetCalSource.execute({'CalSource': 'Home', 'wait': False})
                FF_FiberPos = calibration.get('FF_FiberPos', None)
                SetFlatFieldFiberPos.execute({'FF_FiberPos': FF_FiberPos,
                                              'wait': False})
                log.info(f"Waiting for Octagon (CalSource)")
                WaitForCalSource.execute({'CalSource': 'Home'})
                log.info(f"Waiting for Flat Field Fiber Position")
                WaitForFlatFieldFiberPos.execute(args)
            ## Setup Octagon Lamps and LFCFiber
            elif calsource in ['BrdbandFiber', 'U_gold', 'U_daily', 'Th_daily',
                               'Th_gold', 'LFCFiber']:
                log.info(f"Setting cal source: {calsource}")
                SetCalSource.execute({'CalSource': calsource,
                                      'wait': False})
                log.info(f"Set ND1 Filter Wheel: {calibration.get('CalND1')}")
                SetND1.execute({'CalND1': calibration.get('CalND1'),
                                'wait': False})
                log.info(f"Set ND2 Filter Wheel: {calibration.get('CalND2')}")
                SetND2.execute({'CalND2': calibration.get('CalND2'),
                                'wait': False})
                log.info(f"Waiting for ND1")
                WaitForND1.execute(calibration)
                log.info(f"Waiting for ND2")
                WaitForND2.execute(calibration)
                log.info(f"Waiting for Octagon (CalSource)")
                WaitForCalSource.execute(calibration)
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

            ## Take Actual Exposures
            for j in range(nexp):
                log.info(f"Starting expoure {j+1}/{nexp}")
                StartExposure.execute({})
                WaitForReadout.execute({})
                log.info(f"  Readout has begun")
                WaitForReady.execute({})
                log.info(f"  Readout complete")
            if calsource == 'WideFlat':
                SetFlatFieldFiberPos.execute({'FF_FiberPos': 'Blank'})

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
