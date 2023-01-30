import os
from time import sleep
from packaging import version
from pathlib import Path

import ktl

from ddoitranslatormodule.KPFTranslatorFunction import KPFTranslatorFunction
from .. import (log, KPFException, FailedPreCondition, FailedPostCondition,
                FailedToReachDestination, check_input)
from . import register_script, obey_scriptrun, check_scriptstop, add_script_log
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


class ExecuteSci(KPFTranslatorFunction):
    '''Script which executes a single observation from a science sequence
    
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
        check_input(args, 'Template_Name', allowed_values=['kpf_sci'])
        check_input(args, 'Template_Version', version_check=True, value_min='0.5')
        return True

    @classmethod
    def perform(cls, args, logger, cfg):
        kpfconfig = ktl.cache('kpfconfig')
        kpfguide = ktl.cache('kpfguide')
        exposestatus = ktl.cache('kpfexpose', 'EXPOSE')
        runagitator = kpfconfig['USEAGITATOR'].read(binary=True)

        ## ----------------------------------------------------------------
        ## Setup exposure meter
        ## ----------------------------------------------------------------
        em_exptime = args.get('ExpMeterExpTime', None)
        log.debug(f"ExpMeterExpTime requested {em_exptime:.1f}")
        if em_exptime is not None:
            kpf_expmeter = ktl.cache('kpf_expmeter')
            log.debug(f"Setting ExpMeterExpTime = {em_exptime:.1f}")
            kpf_expmeter['EXPOSURE'].write(em_exptime)
        
        ## ----------------------------------------------------------------
        ## Setup simulcal
        ## ----------------------------------------------------------------
        # Set octagon and ND filters
        if args.get('TakeSimulCal') == True:
            if args.get('AutoNDFilters') == True:
                raise NotImplementedError('AutoNDFilters is not available')
            else:
                SetND1.execute({'CalND1': args['CalND1'], 'wait': False})
                SetND2.execute({'CalND2': args['CalND2'], 'wait': False})
                WaitForND1.execute(args)
                WaitForND2.execute(args)

        check_scriptstop() # Stop here if requested

        ## ----------------------------------------------------------------
        ## Setup kpfexpose
        ## ----------------------------------------------------------------
        WaitForReady.execute({})
        SetObject.execute(args)
        SetExptime.execute(args)
        args['TimedShutter_Scrambler'] = True
        args['TimedShutter_FlatField'] = False
        args['TimedShutter_SimulCal'] = args['TakeSimulCal']
        SetTimedShutters.execute(args)
        args['TriggerExpMeter'] = (args.get('ExpMeterMode', 'monitor') != 'off')
        SetTriggeredDetectors.execute(args)

        ## ----------------------------------------------------------------
        ## Take actual exposures
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
            log.info(f"Starting {args.get('Exptime')} s expoure {j+1}/{nexp} ({args.get('Object')})")
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
    def post_condition(cls, args, logger, cfg):
        return True
