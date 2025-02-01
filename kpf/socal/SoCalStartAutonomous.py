import ktl

from kpf import log, cfg, check_input
from kpf.exceptions import *
from kpf.KPFTranslatorFunction import KPFFunction, KPFScript


class SoCalStartAutonomous(KPFFunction):
    '''Start SoCal's AUTONOMOUS mode by setting AUTONOMOUS=1

    ARGS:
    =====
    None
    '''
    @classmethod
    def pre_condition(cls, args):
        pass

    @classmethod
    def perform(cls, args):
        AUTONOMOUS = ktl.cache('kpfsocal', 'AUTONOMOUS')
        log.info('Setting kpfsocal.AUTONOMOUS = 1')
        AUTONOMOUS.write(1)

    @classmethod
    def post_condition(cls, args):
        AUTONOMOUS = ktl.cache('kpfsocal', 'AUTONOMOUS')
        success = AUTONOMOUS.waitFor("==1", timeout=1)
        if success is False:
            raise FailedToReachDestination('kpfsocal.AUTONOMOUS is not 1')
