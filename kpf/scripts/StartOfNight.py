import ktl

from ddoitranslatormodule.KPFTranslatorFunction import KPFTranslatorFunction
from .. import (log, KPFException, FailedPreCondition, FailedPostCondition,
                FailedToReachDestination, check_input)
from . import register_script, obey_scriptrun, check_scriptstop
from ..ao.SetupAOforKPF import SetupAOforKPF
from ..fiu.InitializeTipTilt import InitializeTipTilt
from ..fiu.ConfigureFIU import ConfigureFIU
from ..spectrograph.SetProgram import SetProgram
from ..spectrograph.WaitForReady import WaitForReady


class StartOfNight(KPFTranslatorFunction):
    '''Send KPF in to a reasonable starting configuration
    
    - set FIU mode to observing
    - initialize tip tilt (set closed loop mode and 0, 0)
    - Setup AO for KPF
    - Configure DCS (ROTDEST and ROTMODE)
    
    ARGS:
    AO (bool) - Open AO hatch, send PCU to KPF, and turn on HEPA? (default=True)
    '''
    @classmethod
    @obey_scriptrun
    def pre_condition(cls, args, logger, cfg):
        return True

    @classmethod
    def perform(cls, args, logger, cfg):
        # Guider
        log.info('Set SCRIPTALLOW to No')
        scriptallow = ktl.cache('kpfconfig', 'SCRIPTALLOW')
        scriptallow.write('No')
        log.info('Configure FIU for "Observing"')
        ConfigureFIU.execute({'mode': 'Observing'})
        log.info('Initialize tip tilt mirror')
        InitializeTipTilt.execute({})
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
