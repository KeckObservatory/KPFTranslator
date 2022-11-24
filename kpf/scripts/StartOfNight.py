import ktl

from ddoitranslatormodule.KPFTranslatorFunction import KPFTranslatorFunction
from .. import (log, KPFException, FailedPreCondition, FailedPostCondition,
                FailedToReachDestination, check_input)
from ..ao.SetupAOforKPF import SetupAOforKPF
from ..fiu.InitializeTipTilt import InitializeTipTilt
from ..fiu.ConfigureFIU import ConfigureFIU
from .SetOutdirs import SetOutdirs
from ..spectrograph.SetProgram import SetProgram
# from ..spectrograph.SetObserver import SetObserver
from .SetObserverFromSchedule import SetObserverFromSchedule


class StartOfNight(KPFTranslatorFunction):
    '''Send KPF in to a reasonable starting configuration
    
    - set FIU mode to observing
    - initialize tip tilt (set closed loop mode and 0, 0)
    - Set OUTDIRS
    - Set PROGNAME
    - Set OBSERVER value based on schedule
    - Setup AO for KPF
    - Configure DCS (ROTDEST and ROTMODE)
    
    ARGS:
    progname - The program ID to set.
    AO (bool) - Close AO hatch, home PCU, and turn on HEPA? (default=True)
    '''
    @classmethod
    def pre_condition(cls, args, logger, cfg):
        check_input(args, 'progname')
#         check_input(args, 'observer')
        return True

    @classmethod
    def perform(cls, args, logger, cfg):
        # Guider
        log.info('Configure FIU for "Observing"')
        ConfigureFIU.execute({'mode': 'Observing'})
        log.info('Initialize tip tilt mirror')
        InitializeTipTilt.execute({})
        # Set Outdirs
        SetOutdirs.execute({})
        # Set progname and observer
        SetProgram.execute(args)
        SetObserverFromSchedule.execute(args)
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
        args_to_add = OrderedDict()
        args_to_add['progname'] = {'type': str,
                                   'help': 'The PROGNAME keyword.'}
        parser = cls._add_args(parser, args_to_add, print_only=False)
        parser = cls._add_bool_arg(parser, 'AO',
            'Configure AO?', default=True)
        return super().add_cmdline_args(parser, cfg)
