import ktl

from kpf.KPFTranslatorFunction import KPFTranslatorFunction
from kpf import (log, KPFException, FailedPreCondition, FailedPostCondition,
                 FailedToReachDestination, check_input)
from kpf.socal.SoCalStopAutonomous import SoCalStopAutonomous


class ParkSoCal(KPFTranslatorFunction):
    '''Parks SoCal. This includes setting AUTONOMOUS to "Manual", closing the
    enclosure, and parking the solar tracker.

    ARGS:
    =====
    None
    '''
    @classmethod
    def pre_condition(cls, args, logger, cfg):
        pass

    @classmethod
    def perform(cls, args, logger, cfg):
        SoCalStopAutonomous.execute({})
        log.info('Parking SoCal')
        kpfsocal = ktl.cache('kpfsocal')
        kpfsocal['ENCCMD'].write('close')
        kpfsocal['EKOSLEW'].write(0)
        kpfsocal['EKOTARGALT'].write(0)
        kpfsocal['EKOTARGAZ'].write(0)
        kpfsocal['EKOMODE'].write(0)
        kpfsocal['EKOSLEW'].write(1)
        kpfsocal['EKOSLEW'].write(0)

    @classmethod
    def post_condition(cls, args, logger, cfg):
        kpfsocal = ktl.cache('kpfsocal')
        timeout = cfg.getfloat('SoCal', 'park_time', fallback=300)
        expr = '($kpfsocal.ENCSTA == 1) '
        expr += 'and ($kpfsocal.EKOHOME == 1)'
        success = ktl.waitFor(expr, timeout=timeout)
        if success is False:
            raise FailedToReachDestination('SoCal failed to park completely')
