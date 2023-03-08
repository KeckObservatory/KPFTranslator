from pathlib import Path

import ktl

from ddoitranslatormodule.KPFTranslatorFunction import KPFTranslatorFunction
from .. import (log, KPFException, FailedPreCondition, FailedPostCondition,
                FailedToReachDestination, check_input)
from . import register_script, obey_scriptrun, check_scriptstop, add_script_log
from ..ao.SetupAOforKPF import SetupAOforKPF
from ..fiu.SetTipTiltGain import SetTipTiltGain
from ..fiu.ConfigureFIU import ConfigureFIU
from ..calbench.SetCalSource import SetCalSource
from ..spectrograph.SetProgram import SetProgram
from ..spectrograph.WaitForReady import WaitForReady
from ..spectrograph.SetSourceSelectShutters import SetSourceSelectShutters


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
        # Disallow cron job calibration scripts
        log.info('Set SCRIPTALLOW to No')
        kpfconfig = ktl.cache('kpfconfig')
        kpfconfig['SCRIPTALLOW'].write('No')
        # Configure FIU
        log.info('Configure FIU for "Observing"')
        ConfigureFIU.execute({'mode': 'Observing'})
        # Configure Source Select Shutters
        SetSourceSelectShutters.execute({'SSS_Science': True, 'SSS_Sky': True})
        # Setup AO
        if args.get('AO', True) is True:
            SetupAOforKPF.execute({})
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
        tip_tilt_gain = cfg.get('tiptilt', 'tiptilt_loop_gain', fallback=0.3)
        log.info(f"Setting default tip tilt loop gain of {tip_tilt_gain}")
        SetTipTiltGain.execute({'GuideLoopGain': tip_tilt_gain})

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
