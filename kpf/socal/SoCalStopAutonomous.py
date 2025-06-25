import ktl

from kpf import log, cfg
from kpf.exceptions import *
from kpf.KPFTranslatorFunction import KPFFunction, KPFScript


class SoCalStopAutonomous(KPFFunction):
    '''Stop SoCal's AUTONOMOUS mode by setting AUTONOMOUS=0

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
        log.info('Setting kpfsocal.AUTONOMOUS = 0')
        AUTONOMOUS.write(0)

    @classmethod
    def post_condition(cls, args):
        AUTONOMOUS = ktl.cache('kpfsocal', 'AUTONOMOUS')
        success = AUTONOMOUS.waitFor("==0", timeout=1)
        if success is False:
            raise FailedToReachDestination('kpfsocal.AUTONOMOUS is not 0')
