import ktl

from kpf.KPFTranslatorFunction import KPFTranslatorFunction
from kpf import (log, KPFException, FailedPreCondition, FailedPostCondition,
                 FailedToReachDestination, check_input)


class WaitForSoCalOnTarget(KPFTranslatorFunction):
    '''Returns True if, within a set timeout, a set of conditions which suggest
    that SoCal is on the Sun accurately evaluate to True.

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
        if on_target == False:
            kpfsocal = ktl.cache('kpfsocal')
            if kpfsocal['ENCSTA'].read(binary=True) != 0:
                log.debug(f'ENCSTA != 0')
            if kpfsocal['EKOONLINE'].read() != 'Online':
                log.debug(f'EKOONLINE != Online')
            if kpfsocal['EKOMODE'].read(binary=True) != 3:
                log.debug(f'EKOMODE != 3')
            if kpfsocal['PYRIRRAD'].read(binary=True) < pyrirrad_threshold:
                log.debug(f'PYRIRRAD < {pyrirrad_threshold}')
            if kpfsocal['AUTONOMOUS'].read(binary=True) != 1:
                log.debug(f'AUTONOMOUS != 1')
            if kpfsocal['IS_OPEN'].read(binary=True) != True:
                log.debug(f'IS_OPEN != True')
            if kpfsocal['IS_TRACKING'].read(binary=True) != True:
                log.debug(f'IS_TRACKING != True')
            if kpfsocal['ONLINE'].read(binary=True) != True:
                log.debug(f'ONLINE != True')
            if kpfsocal['STATE'].read() != 'Tracking':
                log.debug(f'STATE != Tracking')
        return on_target

    @classmethod
    def post_condition(cls, args, logger, cfg):
        pass
