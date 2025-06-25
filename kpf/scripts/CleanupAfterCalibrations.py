import os
from time import sleep
from packaging import version
from pathlib import Path
import numpy as np

import ktl

from kpf import log, cfg
from kpf.exceptions import *
from kpf.KPFTranslatorFunction import KPFFunction, KPFScript
from kpf.ObservingBlocks.ObservingBlock import ObservingBlock
from kpf.calbench.CalLampPower import CalLampPower
from kpf.calbench.IsCalSourceEnabled import IsCalSourceEnabled
from kpf.calbench.SetLFCtoStandbyHigh import SetLFCtoStandbyHigh
from kpf.fiu.ConfigureFIU import ConfigureFIU
from kpf.spectrograph.SetObject import SetObject
from kpf.spectrograph.StopAgitator import StopAgitator
from kpf.spectrograph.WaitForL0File import WaitForL0File
from kpf.spectrograph.WaitForReady import WaitForReady
from kpf.scripts.SetTargetInfo import SetTargetInfo


class CleanupAfterCalibrations(KPFScript):
    '''Script which cleans up after OBs with calibrations.

    Args:
        leave_lamps_on (bool): Leave calibration lamps on when done?
        OB (ObservingBlock): A valid observing block (OB).

    KTL Keywords Used:

    - `kpfconfig.USEAGITATOR`
    - `kpf_expmeter.USETHRESHOLD`

    Functions Called:
    - `kpf.calbench.CalLampPower`
    - `kpf.calbench.IsCalSourceEnabled`
    - `kpf.calbench.SetLFCtoStandbyHigh`
    - `kpf.fiu.ConfigureFIU`
    - `kpf.spectrograph.SetObject`
    - `kpf.spectrograph.StopAgitator`
    - `kpf.spectrograph.WaitForL0File`
    - `kpf.spectrograph.WaitForReady`
    - `kpf.scripts.SetTargetInfo`
    '''
    @classmethod
    def pre_condition(cls, args, OB=None):
        pass

    @classmethod
    def perform(cls, args, OB=None):
        if isinstance(OB, dict):
            OB = ObservingBlock(OB)
        calibrations = OB.Calibrations
        log.info('-------------------------')
        log.info(f"Running {cls.__name__}")
        for i,calibration in enumerate(calibrations):
            log.debug(f"Calibration {i+1}/{len(calibrations)}")
            for key in calibration.to_dict():
                log.debug(f"  {key}: {calibration.get(key)}")
        log.info('-------------------------')

        # Power off lamps
        if args.get('leave_lamps_on', False) == True:
            log.info('Not turning lamps off because leave_lamps_on option was invoked')
        else:
            lamps = set([c.get('CalSource') for c in calibrations])
            for lamp in lamps:
                if IsCalSourceEnabled.execute({'CalSource': lamp}) == True:
                    if lamp in ['Th_daily', 'Th_gold', 'U_daily', 'U_gold',
                                'BrdbandFiber', 'WideFlat']:
                        CalLampPower.execute({'lamp': lamp, 'power': 'off'})
                    if lamp == 'LFCFiber':
                        try:
                            SetLFCtoStandbyHigh.execute({})
                        except Exception as e:
                            log.error('SetLFCtoStandbyHigh failed')
                            log.error(e)
                            try:
                                SendEmail.execute({'Subject': 'ExecuteCals Failed',
                                                   'Message': f'{e}'})
                            except Exception as email_err:
                                log.error(f'Sending email failed')
                                log.error(email_err)




        runagitator = ktl.cache('kpfconfig', 'USEAGITATOR').read(binary=True)
        if runagitator is True:
            StopAgitator.execute({})

        if args.get('stowFIU', True):
            log.info(f"Stowing FIU")
            ConfigureFIU.execute({'mode': 'Stowed'})

        # Turn off exposure meter controlled exposure
        log.debug('Clearing kpf_expmeter.USETHRESHOLD')
        USETHRESHOLD = ktl.cache('kpf_expmeter', 'USETHRESHOLD')
        USETHRESHOLD.write('No')

        # Set OBJECT back to empty string
        log.info('Waiting for readout to finish')
        WaitForReady.execute({})
        SetObject.execute({'Object': ''})

        # Clear target info
        SetTargetInfo.execute({})

        # Write L0 file name to log if can
        WaitForL0File.execute({})

    @classmethod
    def post_condition(cls, args, OB=None):
        pass

    @classmethod
    def add_cmdline_args(cls, parser):
        parser.add_argument('--leave_lamps_on', dest="leave_lamps_on",
                            default=False, action="store_true",
                            help='Leave the lamps on after cleanup phase?')
        return super().add_cmdline_args(parser)
