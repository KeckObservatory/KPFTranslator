import os
from time import sleep
from packaging import version
from pathlib import Path

import ktl

from ddoitranslatormodule.KPFTranslatorFunction import KPFTranslatorFunction
from .. import (log, KPFException, FailedPreCondition, FailedPostCondition,
                FailedToReachDestination, check_input)
from . import register_script, obey_scriptrun, check_scriptstop
from ..spectrograph.SetObject import SetObject
from ..spectrograph.SetExptime import SetExptime
from ..spectrograph.SetTimedShutters import SetTimedShutters
from ..spectrograph.SetTriggeredDetectors import SetTriggeredDetectors
from ..spectrograph.StartAgitator import StartAgitator
from ..spectrograph.StartExposure import StartExposure
from ..spectrograph.StopAgitator import StopAgitator
from ..spectrograph.WaitForReady import WaitForReady
from ..spectrograph.WaitForReadout import WaitForReadout
from ..calbench.CalLampPower import CalLampPower
from ..calbench.SetCalSource import SetCalSource
from ..calbench.SetND1 import SetND1
from ..calbench.SetND2 import SetND2
from ..calbench.WaitForCalSource import WaitForCalSource
from ..calbench.WaitForND1 import WaitForND1
from ..calbench.WaitForND2 import WaitForND2


class ExecuteSciSequence(KPFTranslatorFunction):
    '''Script which executes the observations from a Science OB
    
    - Loops over sequences:
        - Sets OBJECT & EXPTIME
        - Sets exposure meter parameters
        - Sets timed shutters (for simulcal)
        - Sets octagon / simulcal source & ND filters (if not already set)
        - Takes exposures
        - Starts and stops agitator
    
    Can be called by `ddoi_script_functions.execute_observation`.
    '''
    abortable = True

    def abort_execution(args, logger, cfg):
        scriptstop = ktl.cache('kpfconfig', 'SCRIPTSTOP')
        log.warning('Abort recieved, setting kpfconfig.SCRTIPSTOP=Yes')
        scriptstop.write('Yes')

    @classmethod
    @obey_scriptrun
    def pre_condition(cls, OB, logger, cfg):
        check_input(OB, 'Template_Name', allowed_values=['kpf_sci'])
        check_input(OB, 'Template_Version', version_check=True, value_min='0.5')
        return True

    @classmethod
    @register_script(Path(__file__).name, os.getpid())
    def perform(cls, OB, logger, cfg):
        log.info('-------------------------')
        log.info(f"Running {cls.__name__}")
        for key in OB:
            if key not in ['SEQ_Observations']:
                log.debug(f"  {key}: {OB[key]}")
            else:
                log.debug(f"  {key}:")
                for entry in OB[key]:
                    log.debug(f"    {entry}")
        log.info('-------------------------')

        kpfguide = ktl.cache('kpfguide')
        kpfguide['TRIGCUBE'].write('Inactive')
        exposestatus = ktl.cache('kpfexpose', 'EXPOSE')
        runagitator = True # <- read KTL keyword when available

        for seq in OB.get('SEQ_Observations'):
            ## ----------------------------------------------------------------
            ## Setup exposure meter
            ## ----------------------------------------------------------------
            em_exptime = seq.get('ExpMeterExpTime', None)
            log.debug(f"ExpMeterExpTime requested {em_exptime:.1f}")
            if em_exptime is not None:
                kpf_expmeter = ktl.cache('kpf_expmeter')
                log.debug(f"Setting ExpMeterExpTime = {em_exptime:.1f}")
                kpf_expmeter['EXPOSURE'].write(em_exptime)
            
            ## ----------------------------------------------------------------
            ## Setup simulcal
            ## ----------------------------------------------------------------
            # Set octagon and ND filters
            if seq.get('TakeSimulCal') == True:
                if seq.get('AutoNDFilters') == True:
                    raise NotImplementedError('AutoNDFilters is not available')
                else:
                    SetND1.execute({'CalND1': seq['CalND1'], 'wait': False})
                    SetND2.execute({'CalND2': seq['CalND2'], 'wait': False})
                    WaitForND1.execute(seq)
                    WaitForND2.execute(seq)

            check_scriptstop() # Stop here if requested

            ## ----------------------------------------------------------------
            ## Setup kpfexpose
            ## ----------------------------------------------------------------
            WaitForReady.execute({})
            SetObject.execute(seq)
            SetExptime.execute(seq)
            seq['TimedShutter_Scrambler'] = True
            seq['TimedShutter_FlatField'] = False
            log.debug(f"Automatically setting TimedShutter_CaHK: {OB['TriggerCaHK']}")
            seq['TimedShutter_CaHK'] = OB['TriggerCaHK']
            SetTimedShutters.execute(seq)

            OB['TriggerExpMeter'] = (seq.get('ExpMeterMode', 'monitor') != 'off')
            SetTriggeredDetectors.execute(OB)

            ## ----------------------------------------------------------------
            ## Take actual exposures
            ## ----------------------------------------------------------------
            nexp = seq.get('nExp', 1)
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
                log.info(f"Starting {seq.get('Exptime')} s expoure {j+1}/{nexp} ({seq.get('Object')})")
                log.debug('Starting TRIGGER file')
                kpfguide['TRIGGER'].write(1)
                StartExposure.execute({})
                WaitForReadout.execute({})
                log.debug('Stopping TRIGGER file')
                kpfguide['TRIGGER'].write(0)
                log.info(f"Readout has begun")
                if runagitator is True:
                    StopAgitator.execute({})


    @classmethod
    def post_condition(cls, OB, logger, cfg):
        timeout = cfg.get('times', 'kpfexpose_timeout', fallback=0.01)
        expr = f"($kpfexpose.EXPOSE == Ready)"
        success = ktl.waitFor(expr, timeout=timeout)
        return success
