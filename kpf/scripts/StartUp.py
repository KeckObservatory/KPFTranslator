import subprocess

import ktl

from ddoitranslatormodule.KPFTranslatorFunction import KPFTranslatorFunction
from .. import (log, KPFException, FailedPreCondition, FailedPostCondition,
                FailedToReachDestination, check_input)
from ..ao.SetupAOforKPF import SetupAOforKPF
from ..fiu.InitializeTipTilt import InitializeTipTilt
from ..fiu.ConfigureFIU import ConfigureFIU
from .SetOutdirs import SetOutdirs
from ..spectrograph.SetProgram import SetProgram
from ..spectrograph.WaitForReady import WaitForReady
from .SetObserverFromSchedule import SetObserverFromSchedule


class StartUp(KPFTranslatorFunction):
    '''Start KPF software for afternoon setup.
    
    - Set OUTDIRS
    - Set PROGNAME
    - Set OBSERVER value based on schedule
    - bring up GUIs
    
    ARGS:
    progname - The program ID to set.
    '''
    @classmethod
    def pre_condition(cls, args, logger, cfg):
        check_input(args, 'progname')
        return True

    @classmethod
    def perform(cls, args, logger, cfg):
        # Set Outdirs
        WaitForReady.execute({})
        SetOutdirs.execute({})
        # Set progname and observer
        SetProgram.execute(args)
        SetObserverFromSchedule.execute(args)
        # Start GUIs
        fiugui_proc = subprocess.Popen(['/kroot/rel/default/bin/fiu_gui'])
        emgui_proc = subprocess.Popen(['/kroot/rel/default/bin/expmeter_gui'])

    @classmethod
    def post_condition(cls, args, logger, cfg):
        return True
