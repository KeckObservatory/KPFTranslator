from pathlib import Path

import ktl

from kpf.KPFTranslatorFunction import KPFTranslatorFunction
from kpf import (log, KPFException, FailedPreCondition, FailedPostCondition,
                 FailedToReachDestination, check_input)
from kpf.scripts import (register_script, obey_scriptrun, check_scriptstop,
                         add_script_log)
from kpf.ao.SetupAOforKPF import SetupAOforKPF
from kpf.fiu.SetTipTiltGain import SetTipTiltGain
from kpf.fiu.ConfigureFIU import ConfigureFIU
from kpf.calbench.SetCalSource import SetCalSource
from kpf.calbench.CalLampPower import CalLampPower
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
        return True

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
                   "Do you wish to to continue? [Y/n]",
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

        # ---------------------------------
        # Remaining non-AO Actions
        # ---------------------------------
        # Disallow cron job calibration scripts
        log.info('Set ALLOWSCHEDULEDCALS to No')
        kpfconfig = ktl.cache('kpfconfig')
        kpfconfig['ALLOWSCHEDULEDCALS'].write('No')

        # Power on Simulcal lamp
        kpfconfig = ktl.cache('kpfconfig')
        calsource = kpfconfig['SIMULCALSOURCE'].read()
        if calsource in ['U_gold', 'U_daily', 'Th_daily', 'Th_gold']:
            CalLampPower.execute({'lamp': calsource, 'power': 'on'})

        # Configure FIU
        log.info('Configure FIU for "Observing"')
        ConfigureFIU.execute({'mode': 'Observing'})
        # Set DCS rotator parameters
        dcs = ktl.cache('dcs')
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
        # Set tip tilt loop gain
        tip_tilt_gain = cfg.getfloat('tiptilt', 'tiptilt_loop_gain', fallback=0.3)
        log.info(f"Setting default tip tilt loop gain of {tip_tilt_gain}")
        SetTipTiltGain.execute({'GuideLoopGain': tip_tilt_gain})
        # Set Outdirs
        expose = ktl.cache('kpfexpose', 'EXPOSE')
        if expose.read() != 'Ready':
            log.info('Waiting for kpfexpose to be Ready')
            WaitForReady.execute({})
        SetOutdirs.execute({})
        # Set progname and observer
        SetObserverFromSchedule.execute({})


    @classmethod
    def post_condition(cls, args, logger, cfg):
        return True

    @classmethod
    def add_cmdline_args(cls, parser, cfg=None):
        '''The arguments to add to the command line interface.
        '''
        from collections import OrderedDict
        parser = cls._add_bool_arg(parser, 'AO',
            'Configure AO?', default=True)
        return super().add_cmdline_args(parser, cfg)
