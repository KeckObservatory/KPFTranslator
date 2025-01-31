import time
import ktl

from kpf import log, cfg, check_input
from kpf.exceptions import *
from kpf.KPFTranslatorFunction import KPFFunction, KPFScript


class ResetCaHKDetector(KPFFunction):
    '''Resets the Ca HK detector by aborting the exposure

    ARGS:
    =====
    None
    '''
    @classmethod
    def pre_condition(cls, args):
        pass

    @classmethod
    def perform(cls, args):
        expose = ktl.cache('kpf_hk', 'EXPOSE')
        log.warning(f"Resetting/Aborting: kpf_hk.EXPOSE = abort")
        expose.write('abort')
        log.debug('Reset/abort command sent')

    @classmethod
    def post_condition(cls, args):
        expstate = ktl.cache('kpf_hk', 'EXPSTATE')
        timeout = cfg.getfloat('times', 'kpfexpose_reset_time', fallback=10)
        log.warning(f"Waiting for kpf_hk to be Ready")
        success = expstate.waitFor('=="Ready"', timeout=timeout)
        if success is not True:
            raise FailedToReachDestination(expstate.read(), 'Ready')


class ResetExpMeterDetector(KPFFunction):
    '''Resets the exposure meter detector

    ARGS:
    =====
    None
    '''
    @classmethod
    def pre_condition(cls, args):
        pass

    @classmethod
    def perform(cls, args):
        expose = ktl.cache('kpf_expmeter', 'EXPOSE')
        log.warning(f"Resetting: kpf_expmeter.EXPOSE = abort")
        expose.write('Reset')
        log.debug('Reset command sent')

    @classmethod
    def post_condition(cls, args):
        expstate = ktl.cache('kpf_expmeter', 'EXPSTATE')
        timeout = cfg.getfloat('times', 'kpfexpose_reset_time', fallback=10)
        log.warning(f"Waiting for kpf_expmeter to be Ready")
        success = expstate.waitFor('=="Ready"', timeout=timeout)
        if success is not True:
            raise FailedToReachDestination(expstate.read(), 'Ready')


class ResetGreenDetector(KPFFunction):
    '''Resets the kpfgreen detector

    ARGS:
    =====
    None
    '''
    @classmethod
    def pre_condition(cls, args):
        pass

    @classmethod
    def perform(cls, args):
        # Check if the auto reset is already doing this
        current_expstate  = ktl.cache('kpfgreen', 'EXPSTATE')
        current_expstate.read()
        if current_expstate == 'Resetting':
            return
        elif current_expstate == 'Exposing':
            log.warning('Can not send reset during exposure')
            return
        # Send the reset
        expose = ktl.cache('kpfgreen', 'EXPOSE')
        log.warning(f"Resetting: kpfgreen.EXPOSE = Reset")
        expose.write('Reset')
        log.debug('Reset command sent')

    @classmethod
    def post_condition(cls, args):
        timeout = cfg.getfloat('times', 'kpfexpose_reset_time', fallback=10)
        log.warning(f"Waiting for kpfgreen to be Readout or Ready")
        expr = f"($kpfgreen.EXPOSE == 'Ready') or ($kpfgreen.EXPOSE == 'Readout')"
        success = ktl.waitFor(expr, timeout=timeout)
        if success is not True:
            expose = ktl.cache('kpfgreen', 'EXPOSE')
            raise FailedToReachDestination(expose.read(), 'Ready or Readout')
        else:
            kpfexpose = ktl.cache('kpfexpose')
            log.info(f"ResetGreenDetector done")
            log.info(f"kpfexpose.EXPOSE = {kpfexpose['EXPOSE'].read()}")
            log.info(f"kpfexpose.EXPLAINR = {kpfexpose['EXPLAINR'].read()}")
            log.info(f"kpfexpose.EXPLAINNR = {kpfexpose['EXPLAINNR'].read()}")


class ResetRedDetector(KPFFunction):
    '''Resets the kpfred detector

    ARGS:
    =====
    None
    '''
    @classmethod
    def pre_condition(cls, args):
        pass

    @classmethod
    def perform(cls, args):
        # Check if the auto reset is already doing this
        current_expstate = ktl.cache('kpfred', 'EXPSTATE')
        current_expstate.read()
        if current_expstate == 'Resetting':
            return
        elif current_expstate == 'Exposing':
            log.warning('Can not send reset during exposure')
            return
        # Send the reset
        expose = ktl.cache('kpfred', 'EXPOSE')
        log.warning(f"Resetting: kpfred.EXPOSE = Reset")
        expose.write('Reset')
        log.debug('Reset command sent')

    @classmethod
    def post_condition(cls, args):
        timeout = cfg.getfloat('times', 'kpfexpose_reset_time', fallback=10)
        log.warning(f"Waiting for kpfred to be Readout or Ready")
        expr = f"($kpfred.EXPOSE == 'Ready') or ($kpfred.EXPOSE == 'Readout')"
        success = ktl.waitFor(expr, timeout=timeout)
        if success is not True:
            expose = ktl.cache('kpfred', 'EXPOSE')
            raise FailedToReachDestination(expose.read(), 'Ready or Readout')
        else:
            kpfexpose = ktl.cache('kpfexpose')
            log.info(f"ResetRedDetector done")
            log.info(f"kpfexpose.EXPOSE = {kpfexpose['EXPOSE'].read()}")
            log.info(f"kpfexpose.EXPLAINR = {kpfexpose['EXPLAINR'].read()}")
            log.info(f"kpfexpose.EXPLAINNR = {kpfexpose['EXPLAINNR'].read()}")


class ResetDetectors(KPFFunction):
    '''Resets the kpfexpose service by setting kpfexpose.EXPOSE = Reset

    Description from Will Deich:
    This sets EXPOSE=Reset for the appropriate service.  For the 
    ktlcamerad services, that just means, “even though you’ve not received
    (from camerad) the normal sequence of messages for a completed exposure,
    pretend everything is fine for starting a new exposure.”
    
    ARGS:
    =====
    None
    '''
    @classmethod
    def pre_condition(cls, args):
        pass

    @classmethod
    def perform(cls, args):
        kpfexpose = ktl.cache('kpfexpose')
        log.warning(f"Resetting: kpfexpose.EXPOSE = Reset")
        kpfexpose['EXPOSE'].write('Reset')
        log.debug('Reset command sent')

    @classmethod
    def post_condition(cls, args):
        timeout = cfg.getfloat('times', 'kpfexpose_reset_time', fallback=10)
        log.debug(f'Waiting {timeout:.1f} s for EXPOSE to be Readout or Ready')
        expr = f"($kpfexpose.EXPOSE == 'Ready') or ($kpfexpose.EXPOSE == 'Readout')"
        log.warning(f"Waiting for kpfexpose to be Ready or Readout")
        success = ktl.waitFor(expr, timeout=timeout)
        if success is not True:
            kpfexposeexpose = ktl.cache('kpfexpose', 'EXPOSE')
            raise FailedToReachDestination(kpfexposeexpose.read(), 'Ready or Readout')
        else:
            kpfexpose = ktl.cache('kpfexpose')
            log.info(f"Reset detectors done")
            log.info(f"kpfexpose.EXPOSE = {kpfexpose['EXPOSE'].read()}")
            log.info(f"kpfexpose.EXPLAINR = {kpfexpose['EXPLAINR'].read()}")
            log.info(f"kpfexpose.EXPLAINNR = {kpfexpose['EXPLAINNR'].read()}")


class RecoverDetectors(KPFFunction):
    '''Try to examine the state of all detectors an run the appropriate recovery
    
    ARGS:
    =====
    None
    '''
    @classmethod
    def pre_condition(cls, args):
        pass

    @classmethod
    def perform(cls, args):
        log.warning('Attempting a detector recovery')
        timeout = cfg.getfloat('times', 'kpfexpose_reset_time', fallback=10)
        kpfmon = ktl.cache('kpfmon')
        camera_status = kpfmon['CAMSTATESTA'].read()
        if camera_status == 'OK':
            log.warning('No camera error state detected by kpfmon')
            explainnr = ktl.cache('kpfexpose', 'EXPLAINNR')
            explainnr_str = explainnr.read()
            if explainnr_str.find('hk:') >= 0:
                log.warning('kpfexpose.EXPLAINNR contains hk')
                ResetCaHKDetector.execute({})
        elif camera_status == 'ERROR':
            if kpfmon['G_STATESTA'].read() == 'ERROR':
                ResetGreenDetector.execute({})
            if kpfmon['R_STATESTA'].read() == 'ERROR':
                ResetRedDetector.execute({})
            if kpfmon['H_STATESTA'].read() == 'ERROR':
                ResetCaHKDetector.execute({})
            if kpfmon['E_STATESTA'].read() == 'ERROR':
                ResetExpMeterDetector.execute({})
        else:
            log.warning(f'kpfmon.CAMSTATESTA={camera_status}. No action taken.')

    @classmethod
    def post_condition(cls, args):
        timeout = cfg.getfloat('times', 'kpfexpose_reset_time', fallback=10)
        log.debug(f'Waiting {timeout:.1f} s for EXPOSE to be Readout or Ready')
        expr = f"($kpfexpose.EXPOSE == 'Ready') or ($kpfexpose.EXPOSE == 'Readout')"
        log.warning(f"Waiting for kpfexpose to be Ready or Readout")
        success = ktl.waitFor(expr, timeout=timeout)
        if success is not True:
            kpfexposeexpose = ktl.cache('kpfexpose', 'EXPOSE')
            raise FailedToReachDestination(kpfexposeexpose.read(), 'Ready or Readout')
        else:
            kpfexpose = ktl.cache('kpfexpose')
            log.info(f"Reset detectors done")
            log.info(f"kpfexpose.EXPOSE = {kpfexpose['EXPOSE'].read()}")
            log.info(f"kpfexpose.EXPLAINR = {kpfexpose['EXPLAINR'].read()}")
            log.info(f"kpfexpose.EXPLAINNR = {kpfexpose['EXPLAINNR'].read()}")



