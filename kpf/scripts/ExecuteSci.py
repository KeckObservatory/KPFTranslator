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
from kpf.spectrograph.QueryFastReadMode import QueryFastReadMode
from kpf.spectrograph.SetObject import SetObject
from kpf.spectrograph.SetExpTime import SetExpTime
from kpf.spectrograph.SetTimedShutters import SetTimedShutters
from kpf.spectrograph.SetTriggeredDetectors import SetTriggeredDetectors
from kpf.spectrograph.StartAgitator import StartAgitator
from kpf.spectrograph.StartExposure import StartExposure
from kpf.spectrograph.StopAgitator import StopAgitator
from kpf.spectrograph.WaitForReady import WaitForReady
from kpf.spectrograph.WaitForReadout import WaitForReadout
from kpf.calbench.SetND1 import SetND1
from kpf.calbench.SetND2 import SetND2
from kpf.calbench.WaitForND1 import WaitForND1
from kpf.calbench.WaitForND2 import WaitForND2
from kpf.calbench.PredictNDFilters import PredictNDFilters
from kpf.expmeter.PredictExpMeterParameters import PredictExpMeterParameters
from kpf.expmeter.SetExpMeterExpTime import SetExpMeterExpTime
from kpf.expmeter.SetupExpMeter import SetupExpMeter


class ExecuteSci(KPFTranslatorFunction):
    '''Script which executes a single observation from a science sequence

    This must have arguments as input, either from a file using the `-f` command
    line tool, or passed in from the execution engine.

    ARGS:
    =====
    :args: `dict` An observation component of a science observing block (OB).
    '''
    abortable = True

    @classmethod
    def pre_condition(cls, args, logger, cfg):
        check_input(args, 'Template_Name', allowed_values=['kpf_sci'])
        check_input(args, 'Template_Version', version_check=True, value_min='0.5')

    @classmethod
    def perform(cls, args, logger, cfg):
        log.info('-------------------------')
        log.info(f"Running {cls.__name__}")
        for key in args:
            log.debug(f"  {key}: {args[key]}")
        log.info('-------------------------')

        kpfconfig = ktl.cache('kpfconfig')
        kpfguide = ktl.cache('kpfguide')
        exposestatus = ktl.cache('kpfexpose', 'EXPOSE')
        runagitator = kpfconfig['USEAGITATOR'].read(binary=True)
        fast_read_mode = QueryFastReadMode.execute({})

        ## ----------------------------------------------------------------
        ## Setup exposure meter
        ## ----------------------------------------------------------------
        args = SetupExpMeter.execute(args)
        if args.get('AutoExpMeter', False) in [True, 'True']:
            em_params = PredictExpMeterParameters.execute(args)
            EM_ExpTime = em_params.get('ExpMeterExpTime', None)
            log.debug(f'Automatically setting EM ExpTime')
            args['ExpMeterExpTime'] = EM_ExpTime
        else:
            EM_ExpTime = args.get('ExpMeterExpTime', None)

        if EM_ExpTime is not None:
            log.debug(f"Setting ExpMeterExpTime = {args['ExpMeterExpTime']:.1f}")
            SetExpMeterExpTime.execute(args)

        ## ----------------------------------------------------------------
        ## Setup simulcal
        ## ----------------------------------------------------------------
        # Set octagon and ND filters
        if args.get('TakeSimulCal') == True:
            if args.get('AutoNDFilters') == True:
                TARGET_TEFF = ktl.cache('kpf_expmeter', 'TARGET_TEFF').read(binary=True)
                TARGET_GMAG = float(kpfconfig['TARGET_GMAG'].read())
                result = PredictNDFilters.execute({'Gmag': TARGET_GMAG,
                                                   'Teff': TARGET_TEFF,
                                                   'ExpTime': args.get('ExpTime')})
                args['CalND1'] = result['CalND1']
                args['CalND2'] = result['CalND2']
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

        # Turn off writing of guider FITS cube if exposure time is long
        exptime = args.get('ExpTime')
        max_for_cube = cfg.getfloat('times', 'max_exptime_for_guide_cube', fallback=60)
        if float(exptime) > max_for_cube:
            kpfguide = ktl.cache('kpfguide')
            kpfguide['TRIGCUBE'].write('Inactive')

        args['TimedShutter_Scrambler'] = True
        args['TimedShutter_FlatField'] = False
        args['TimedShutter_SimulCal'] = args['TakeSimulCal']
        SetTimedShutters.execute(args)
        SetTriggeredDetectors.execute(args)

        check_scriptstop() # Stop here if requested

        ## ----------------------------------------------------------------
        ## Take actual exposures
        ## ----------------------------------------------------------------
        nexp = int(args.get('nExp', 1))
        # If we are in fast read mode, turn on agitator once
        if runagitator and fast_read_mode:
            StartAgitator.execute({})
        for j in range(nexp):
            check_scriptstop() # Stop here if requested
            # Wait for current exposure to readout
            if exposestatus.read() != 'Ready':
                log.info(f"Waiting for kpfexpose to be Ready")
                WaitForReady.execute({})
                log.info(f"Readout complete")
                check_scriptstop() # Stop here if requested
            # Start next exposure
            if runagitator and not fast_read_mode:
                StartAgitator.execute({})
            msg = f"Starting {args.get('ExpTime')} s exposure {j+1}/{nexp} ({args.get('Object')})"
            log.info(msg)
            kpfconfig['SCRIPTMSG'].write(msg)
            StartExposure.execute({})
            WaitForReadout.execute({})
            msg = f"Readout has begun for exposure {j+1}/{nexp}"
            log.info(msg)
            kpfconfig['SCRIPTMSG'].write(msg)
            if runagitator and not fast_read_mode:
                StopAgitator.execute({})
        # If we are in fast read mode, turn off agitator at end
        if runagitator and fast_read_mode:
            StopAgitator.execute({})

    @classmethod
    def post_condition(cls, args, logger, cfg):
        pass
