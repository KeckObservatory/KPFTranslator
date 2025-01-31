import os
import traceback
from time import sleep
from packaging import version
from pathlib import Path

import ktl

from kpf import log, cfg, check_input
from kpf.exceptions import *
from kpf.KPFTranslatorFunction import KPFFunction, KPFScript
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


class ExecuteSci(KPFFunction):
    '''Script which executes a single observation from a science sequence

    This must have arguments as input, either from a file using the `-f` command
    line tool, or passed in from the execution engine.

    ARGS:
    =====
    :observation: `dict` An observation component of a science observing block (OB).
    '''
    abortable = True

    @classmethod
    def pre_condition(cls, observation):
        pass

    @classmethod
    def perform(cls, observation):
        log.info('-------------------------')
        log.info(f"Running {cls.__name__}")
        log.info('-------------------------')

        kpfconfig = ktl.cache('kpfconfig')
        kpfguide = ktl.cache('kpfguide')
        exposestatus = ktl.cache('kpfexpose', 'EXPOSE')
        runagitator = kpfconfig['USEAGITATOR'].read(binary=True)
        fast_read_mode = QueryFastReadMode.execute({})

        ## ----------------------------------------------------------------
        ## Setup exposure meter
        ## ----------------------------------------------------------------
        observation = SetupExpMeter.execute(observation)
        if observation.get('AutoExpMeter', False) in [True, 'True']:
            em_params = PredictExpMeterParameters.execute(observation)
            EM_ExpTime = em_params.get('ExpMeterExpTime', None)
            log.debug(f'Automatically setting EM ExpTime')
            observation['ExpMeterExpTime'] = EM_ExpTime
        else:
            EM_ExpTime = observation.get('ExpMeterExpTime', None)

        if EM_ExpTime is not None:
            log.debug(f"Setting ExpMeterExpTime = {observation['ExpMeterExpTime']:.1f}")
            SetExpMeterExpTime.execute(observation)

        ## ----------------------------------------------------------------
        ## Setup simulcal
        ## ----------------------------------------------------------------
        # Set octagon and ND filters
        if observation.get('TakeSimulCal') == True:
            if observation.get('AutoNDFilters') == True:
                TARGET_TEFF = ktl.cache('kpf_expmeter', 'TARGET_TEFF').read(binary=True)
                TARGET_GMAG = float(kpfconfig['TARGET_GMAG'].read())
                result = PredictNDFilters.execute({'Gmag': TARGET_GMAG,
                                                   'Teff': TARGET_TEFF,
                                                   'ExpTime': observation.get('ExpTime')})
                observation['CalND1'] = result['CalND1']
                observation['CalND2'] = result['CalND2']
            SetND1.execute({'CalND1': observation['CalND1'], 'wait': False})
            SetND2.execute({'CalND2': observation['CalND2'], 'wait': False})
            WaitForND1.execute(observation)
            WaitForND2.execute(observation)

        check_scriptstop() # Stop here if requested

        ## ----------------------------------------------------------------
        ## Setup kpfexpose
        ## ----------------------------------------------------------------
        WaitForReady.execute({})
        SetObject.execute(observation)
        SetExpTime.execute(observation)

        # Turn off writing of guider FITS cube if exposure time is long
        exptime = observation.get('ExpTime')
        max_for_cube = cfg.getfloat('times', 'max_exptime_for_guide_cube', fallback=60)
        if float(exptime) > max_for_cube:
            kpfguide = ktl.cache('kpfguide')
            kpfguide['TRIGCUBE'].write('Inactive')

        observation['TimedShutter_Scrambler'] = True
        observation['TimedShutter_FlatField'] = False
        observation['TimedShutter_SimulCal'] = observation['TakeSimulCal']
        SetTimedShutters.execute(observation)
        SetTriggeredDetectors.execute(observation)

        check_scriptstop() # Stop here if requested

        ## ----------------------------------------------------------------
        ## Take actual exposures
        ## ----------------------------------------------------------------
        nexp = int(observation.get('nExp', 1))
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
            log.info(f"Starting {observation.get('ExpTime')} s expoure {j+1}/{nexp} ({observation.get('Object')})")
            StartExposure.execute({})
            WaitForReadout.execute({})
            log.info(f"Readout has begun")
            if runagitator and not fast_read_mode:
                StopAgitator.execute({})
        # If we are in fast read mode, turn off agitator at end
        if runagitator and fast_read_mode:
            StopAgitator.execute({})

    @classmethod
    def post_condition(cls, observation):
        pass
