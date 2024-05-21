import ktl

from kpf.KPFTranslatorFunction import KPFTranslatorFunction
from kpf import (log, KPFException, FailedPreCondition, FailedPostCondition,
                 FailedToReachDestination, check_input)


class WaitForSoCalOnTarget(KPFTranslatorFunction):
    '''

    ARGS:
    =====
    None
    '''
    @classmethod
    def pre_condition(cls, args, logger, cfg):
        pass

    @classmethod
    def perform(cls, args, logger, cfg):
        timeout = cfg.getfloat('SoCal', 'enclosure_status_time', fallback=10)
        pyrirrad_threshold = cfg.getfloat('SoCal', 'pyrirrad_threshold', fallback=1000)
        expr = '($kpfsocal.ENCSTA == 0) '
        expr += 'and ($kpfsocal.EKOONLINE == Online)'
        expr += 'and ($kpfsocal.EKOMODE == 3)'
        expr += f'and ($kpfsocal.PYRIRRAD > {pyrirrad_threshold})'
        expr += 'and ($kpfsocal.AUTONOMOUS == 1)'
        expr += 'and ($kpfsocal.CAN_OPEN == True)'
        expr += 'and ($kpfsocal.IS_OPEN == True)'
        expr += 'and ($kpfsocal.IS_TRACKING == True)'
        expr += 'and ($kpfsocal.ONLINE == True)'
        expr += 'and ($kpfsocal.STATE == Tracking)'
        on_target = ktl.waitFor(expr, timeout=timeout)
        msg = {True: 'On Target', False: 'NOT On Target'}[on_target]
        print(msg)
        return on_target

    @classmethod
    def post_condition(cls, args, logger, cfg):
        pass
