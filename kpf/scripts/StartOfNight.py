import ktl

from ddoitranslatormodule.KPFTranslatorFunction import KPFTranslatorFunction
from .. import (log, KPFException, FailedPreCondition, FailedPostCondition,
                FailedToReachDestination, check_input)
from ..ao.SetupAOforKPF import SetupAOforKPF
from ..fiu.InitializeTipTilt import InitializeTipTilt
from ..fiu.ConfigureFIU import ConfigureFIU
from .SetOutdirs import SetOutdirs
from ..spectrograph.SetProgram import SetProgram
from ..spectrograph.SetObserver import SetObserver


class StartOfNight(KPFTranslatorFunction):
    '''Send KPF in to a reasonable starting configuration
    
    - kpfguide.SENSORSETP = -40
    - initialize tip tilt (set closed loop mode and 0, 0)
    - set FIU mode to observing
    - Seup AO
    - Set OUTDIRS
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
        # Setup AO
        if args.get('AO', True) is True:
            SetupAOforKPF.execute({})
        # Set progname and observer
        SetProgram.execute(args)
#         SetObserver.execute(args)

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
#         args_to_add['observer'] = {'type': str,
#                                    'help': 'The OBSERVER keyword.'}
        parser = cls._add_args(parser, args_to_add, print_only=False)
        parser = cls._add_bool_arg(parser, 'AO',
            'Configure AO?', default=True)
        return super().add_cmdline_args(parser, cfg)
