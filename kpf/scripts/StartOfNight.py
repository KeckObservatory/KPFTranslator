from pathlib import Path

import ktl

from kpf.KPFTranslatorFunction import KPFTranslatorFunction
from kpf import (log, KPFException, FailedPreCondition, FailedPostCondition,
                 FailedToReachDestination, check_input)
from kpf.scripts import (register_script, obey_scriptrun, check_scriptstop,
                         add_script_log)
from kpf.ao.ControlAOHatch import ControlAOHatch
from kpf.ao.SetupAOforKPF import SetupAOforKPF
from kpf.fiu.SetTipTiltGain import SetTipTiltGain
from kpf.fiu.ConfigureFIU import ConfigureFIU
from kpf.fiu.TestTipTiltMirrorRange import TestTipTiltMirrorRange
from kpf.calbench.SetCalSource import SetCalSource
from kpf.calbench.CalLampPower import CalLampPower
from kpf.guider.SetGuiderGain import SetGuiderGain
from kpf.spectrograph.WaitForReady import WaitForReady
from kpf.spectrograph.SetSourceSelectShutters import SetSourceSelectShutters
from kpf.utils.SetOutdirs import SetOutdirs
from kpf.utils.SetObserverFromSchedule import SetObserverFromSchedule


class StartOfNight(KPFTranslatorFunction):
    '''Send KPF in to a reasonable starting configuration
    
    - set FIU mode to observing
    - Setup AO for KPF
    - Configure DCS (ROTDEST and ROTMODE)
    
    ARGS:
    =====
    :AO: (bool) Open AO hatch, send PCU to KPF, and turn on HEPA? (default=True)
    '''
    @classmethod
    @obey_scriptrun
    def pre_condition(cls, args, logger, cfg):
        pass

    @classmethod
    @add_script_log(Path(__file__).name.replace(".py", ""))
    def perform(cls, args, logger, cfg):
        log.info(f"Running KPF Start of Night script")

        # Setup AO
        if args.get('AO', True) is True:
            # ---------------------------------
            # User Verification
            # ---------------------------------
            msg = ["",
                   "--------------------------------------------------------------",
                   "This script will configure the FIU and AO bench for observing.",
                   "The AO bench area should be clear of personnel before proceeding.",
                   "Do you wish to to continue?",
                   "(y/n) [y]:",
                   "--------------------------------------------------------------",
                   "",
                   ]
            for line in msg:
                print(line)
            user_input = input()
            if user_input.lower() in ['n', 'no', 'q', 'quit', 'abort']:
                log.warning(f'User aborted Start Of Night')
                return
            else:
                SetupAOforKPF.execute({})
                log.info('Open AO hatch')
                try:
                    ControlAOHatch.execute({'destination': 'open'})
                except FailedToReachDestination:
                    log.error(f"AO hatch did not move successfully")
                    print()
                    print('----------------------------------------------------------')
                    print('AO hatch reported problems moving. Make sure stars are')
                    print('visible on guide camera before proceeding.')
                    print('----------------------------------------------------------')
                    print()

        # ---------------------------------
        # Remaining non-AO Actions
        # ---------------------------------
        # Disallow cron job calibration scripts
        log.info('Set ALLOWSCHEDULEDCALS to No')
        kpfconfig = ktl.cache('kpfconfig')
        kpfconfig['ALLOWSCHEDULEDCALS'].write('No')

        # Configure FIU
        log.info('Configure FIU for "Observing"')
        ConfigureFIU.execute({'mode': 'Observing'})
        # Set DCS rotator parameters
        dcs = ktl.cache('dcs1')
        inst = dcs['INSTRUME'].read()
        if inst == 'KPF':
            log.info(f"Setting dcs.ROTDEST = 0")
            dcs['ROTDEST'].write(0)
            log.info(f"Setting dcs.ROTMODE = stationary")
            dcs['ROTMODE'].write('stationary')
        else:
            log.warning(f"Instrument is {inst}, not configuring DCS")

        # Report Agitator status
        runagitator = kpfconfig['USEAGITATOR'].read(binary=True)
        if runagitator is True:
            log.info(f"Agitator use is enabled")
        else:
            log.warning(f"Agitator use is disabled for tonight")
        # Pre-configure cal source
        calsource = kpfconfig['SIMULCALSOURCE'].read()
        log.info(f"Setting simultaneous CalSource/Octagon: {calsource}")
        SetCalSource.execute({'CalSource': calsource, 'wait': True})
        # Power on Simulcal lamp if needed
        if calsource in ['U_gold', 'U_daily', 'Th_daily', 'Th_gold']:
            CalLampPower.execute({'lamp': calsource, 'power': 'on'})
        # Set tip tilt loop gain to default value
        kpfguide = ktl.cache('kpfguide')
        tip_tilt_gain = cfg.getfloat('tiptilt', 'tiptilt_loop_gain', fallback=0.3)
        log.info(f"Setting default tip tilt loop gain of {tip_tilt_gain}")
        SetTipTiltGain.execute({'GuideLoopGain': tip_tilt_gain})
        # Set tip tilt loop detection threshold to default value
        detect_snr = cfg.getfloat('tiptilt', 'detect_snr', fallback=7)
        log.info(f"Setting default tip tilt detection SNR of {detect_snr}")
        kpfguide['OBJECT_INTENSITY'].write(detect_snr)
        # Set tip tilt loop detection area to default value
        detect_area = cfg.getfloat('tiptilt', 'detect_area', fallback=100)
        log.info(f"Setting default tip tilt detection area of {detect_area}")
        kpfguide['OBJECT_AREA'].write(detect_area)
        # Set tip tilt loop deblend parameter to default value
        deblend = cfg.getfloat('tiptilt', 'deblend', fallback=1)
        log.info(f"Setting default tip tilt deblending parameter of {deblend}")
        kpfguide['OBJECT_DBCONT'].write(detect_snr)
        # Set DAR parameter to default value
        log.info(f"Ensuring DAR correction is on")
        kpfguide['DAR_ENABLE'].write('Yes')
        # Set Outdirs
        expose = ktl.cache('kpfexpose', 'EXPOSE')
        if expose.read() != 'Ready':
            log.info('Waiting for kpfexpose to be Ready')
            WaitForReady.execute({})
        SetOutdirs.execute({})
        # Set guider gain to high for initial acquisition and focus
        SetGuiderGain.execute({'GuideCamGain': 'high'})
        # Set progname and observer
        SetObserverFromSchedule.execute({})
        # Summarize Detector Disabled States
        cahk_enabled = kpfconfig['CA_HK_ENABLED'].read(binary=True)
        if cahk_enabled is False:
            log.warning(f"The CA_HK detector is disabled tonight")
        green_enabled = kpfconfig['GREEN_ENABLED'].read(binary=True)
        if green_enabled is False:
            log.warning(f"The Green detector is disabled tonight")
        red_enabled = kpfconfig['RED_ENABLED'].read(binary=True)
        if red_enabled is False:
            log.warning(f"The Red detector is disabled tonight")
        expmeter_enabled = kpfconfig['EXPMETER_ENABLED'].read(binary=True)
        if expmeter_enabled is False:
            log.warning(f"The ExpMeter detector is disabled tonight")

    @classmethod
    def post_condition(cls, args, logger, cfg):
        pass

    @classmethod
    def add_cmdline_args(cls, parser, cfg=None):
        '''The arguments to add to the command line interface.
        '''
        parser.add_argument("--noAO", dest="AO",
                            default=True, action="store_false",
                            help="Skip configuring AO?")
        return super().add_cmdline_args(parser, cfg)
