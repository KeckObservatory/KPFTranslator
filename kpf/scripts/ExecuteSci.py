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
from ..spectrograph.SetExpTime import SetExpTime
from ..spectrograph.SetTimedShutters import SetTimedShutters
from ..spectrograph.SetTriggeredDetectors import SetTriggeredDetectors
from ..spectrograph.StartAgitator import StartAgitator
from ..spectrograph.StartExposure import StartExposure
from ..spectrograph.StopAgitator import StopAgitator
from ..spectrograph.WaitForReady import WaitForReady
from ..spectrograph.WaitForReadout import WaitForReadout
from ..calbench.SetND1 import SetND1
from ..calbench.SetND2 import SetND2
from ..calbench.WaitForND1 import WaitForND1
from ..calbench.WaitForND2 import WaitForND2
from ..expmeter.PredictExpMeterParameters import predict_expmeter_parameters
from ..expmeter.SetExpMeterExpTime import SetExpMeterExpTime


class ExecuteSci(KPFTranslatorFunction):
    '''Script which executes a single observation from a science sequence

    This must have arguments as input, either from a file using the `-f` command
    line tool, or passed in from the execution engine.

    Can be called by `ddoi_script_functions.execute_observation`.

    ARGS:
    =====
    None
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
    @add_script_log(Path(__file__).name.replace(".py", ""))
    def perform(cls, args, logger, cfg):
        kpfconfig = ktl.cache('kpfconfig')
        kpfguide = ktl.cache('kpfguide')
        exposestatus = ktl.cache('kpfexpose', 'EXPOSE')
        runagitator = kpfconfig['USEAGITATOR'].read(binary=True)

        ## ----------------------------------------------------------------
        ## Setup exposure meter
        ## ----------------------------------------------------------------
        if args.get('ExpMeterMode', 'monitor') == 'monitor':
            pass
        else:
            log.warning(f"Only monitor mode is available right now")

        if args.get('AutoExpMeter', False) == True:
            em_params = predict_expmeter_parameters(args.get('Gmag'))
            args['ExpMeterExpTime'] = em_params
        else:
            pass

        log.debug(f"Setting ExpMeterExpTime = {args['ExpMeterExpTime']:.1f}")
        SetExpMeterExpTime.execute(args)

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
        SetExpTime.execute(args)
        args['TimedShutter_Scrambler'] = True
        args['TimedShutter_FlatField'] = False
        args['TimedShutter_SimulCal'] = args['TakeSimulCal']
        SetTimedShutters.execute(args)
        args['TriggerExpMeter'] = (args.get('ExpMeterMode', 'monitor') != 'off')
        SetTriggeredDetectors.execute(args)

        check_scriptstop() # Stop here if requested

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
            log.info(f"Starting {args.get('ExpTime')} s expoure {j+1}/{nexp} ({args.get('Object')})")
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
