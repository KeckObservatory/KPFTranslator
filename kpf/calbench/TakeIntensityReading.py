import time
import ktl

from kpf.KPFTranslatorFunction import KPFTranslatorFunction
from kpf import (log, KPFException, FailedPreCondition, FailedPostCondition,
                 FailedToReachDestination, check_input)
from kpf.utils.SendEmail import SendEmail


class TakeIntensityReading(KPFTranslatorFunction):
    '''# Description
    Insert the intensity monitor (aka "cal diode") in to the beam and record
    a measurement of the cal lamp intensity.
    
    # Parameters
    None
    '''
    @classmethod
    def pre_condition(cls, args, logger, cfg):
        pass

    @classmethod
    def perform(cls, args, logger, cfg):
        kpfcal = ktl.cache('kpfcal')
        intensemon = ktl.cache('kpflamps', 'INTENSEMON')

        # Turn on intensity monitor
        if intensemon.read() == 'Off':
            log.debug('Turning kpflamps.INTENSEMON on')
            intensemon.write('On')
            boottime = cfg.getfloat('times', 'intenmon_boot_time', fallback=5)
            time.sleep(boottime)

        # Verify serial connection is active
        if kpfcal['SERIALCONN'].read() == 'Off':
            log.debug('Initiating serial connection')
            kpfcal['SERIALCONN'].write('On')
            expr = f"($kpfcal.SERIALCONN == 'On')"
            boottime = cfg.getfloat('times', 'intenmon_boot_time', fallback=5)
            success = ktl.waitFor(expr, timeout=boottime)
            if success is False:
                msg = f'Intensity monitor serial connection is Off'
                log.error(msg)
                SendEmail.execute({'Subject': 'TakeIntensityReading Failed',
                                   'Message': f'{msg}'})

        # Move sensor in to beam
        log.info('Moving Intensity Monitor in to beam')
        kpfcal['INTENMON'].write('Boresight')
        # Set averaging
        navg = cfg.getfloat('times', 'intenmon_avg_time', fallback=60)
        log.info(f'Starting measurement: NAVG={navg}')
        kpfcal['NAVG'].write(navg)
        kpfcal['AVG'].write('On')

        # Check whether measuring is taking place
        expr = f"($kpfcal.MEASURING == 'Yes')"
        success = ktl.waitFor(expr, timeout=5)
        if success is False:
            msg = f'Intensity monitor is not measuring'
            log.error(msg)
            SendEmail.execute({'Subject': 'TakeIntensityReading Failed',
                               'Message': f'{msg}'})

        # Wait for readings to be complete
        expr = f"($kpfcal.AVG == 'Off')"
        success = ktl.waitFor(expr, timeout=navg+10)
        if success is False:
            msg = f'Intensity monitor measurement timed out'
            log.error(msg)
            SendEmail.execute({'Subject': 'TakeIntensityReading Failed',
                               'Message': f'{msg}'})

        # Move sensor out of beam
        log.info('Moving Intensity Monitor out of beam')
        kpfcal['INTENMON'].write('Out')

        # Turn off intensity monitor
        log.debug('Turning kpflamps.INTENSEMON off')
        intensemon.write('Off')
        log.debug('Turning kpfcal.SERIALCONN off')
        kpfcal['SERIALCONN'].write('Off')

    @classmethod
    def post_condition(cls, args, logger, cfg):
        pass
