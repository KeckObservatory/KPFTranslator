import os
from time import sleep
from packaging import version
from pathlib import Path
import yaml

import ktl

from ddoitranslatormodule.KPFTranslatorFunction import KPFTranslatorFunction
from .. import (log, KPFException, FailedPreCondition, FailedPostCondition,
                FailedToReachDestination, check_input)
from . import register_script, obey_scriptrun, verify_cleared, check_scriptstop
from ..spectrograph.SetObject import SetObject
from ..spectrograph.SetExptime import SetExptime
from ..spectrograph.SetSourceSelectShutters import SetSourceSelectShutters
from ..spectrograph.SetTimedShutters import SetTimedShutters
from ..spectrograph.SetTriggeredDetectors import SetTriggeredDetectors
from ..spectrograph.StartAgitator import StartAgitator
from ..spectrograph.StartExposure import StartExposure
from ..spectrograph.StopAgitator import StopAgitator
from ..spectrograph.WaitForReady import WaitForReady
from ..spectrograph.WaitForReadout import WaitForReadout


class ExecuteSciSequence(KPFTranslatorFunction):
    '''Script which executes the observations from a Science OB
    
    - Loops over sequences:
        - Sets OBJECT & EXPTIME
        - Sets exposure meter parameters
        - Sets timed shutters (for simulcal)
        - Sets octagon / silumcal source & ND filters (if not already set)
        - Takes exposures
        - Starts and stops agitator
    
    Can be called by `ddoi_script_functions.execute_observation`.
    '''
    abortable = True

    def abort_execution(args, logger, cfg):
        scriptstop = ktl.cache('kpfconfig', 'SCRIPTSTOP')
        log.warning('Abort recieved, setting kpfconfig.SCRTIPSTOP=Yes')
        scriptstop.write('Yes')

    @classmethod
    @obey_scriptrun
    def pre_condition(cls, OB, logger, cfg):
        check_input(OB, 'Template_Name', allowed_values=['kpf_sci'])
        check_input(OB, 'Template_Version', version_check=True, value_min='0.4')
        return True

    @classmethod
    @register_script(Path(__file__).name, os.getpid())
    def perform(cls, OB, logger, cfg):
        log.info('-------------------------')
        log.info(f"Running ExecuteObservingSequence")
        for key in OB:
            if key not in ['SEQ_Observations']:
                log.debug(f"  {key}: {OB[key]}")
            else:
                log.debug(f"  {key}:")
                for entry in OB[key]:
                    log.debug(f"    {entry}")
        log.info('-------------------------')


    @classmethod
    @verify_cleared
    def post_condition(cls, OB, logger, cfg):
        timeout = cfg.get('times', 'kpfexpose_timeout', fallback=0.01)
        expr = f"($kpfexpose.EXPOSE == Ready)"
        success = ktl.waitFor(expr, timeout=timeout)
        return success
