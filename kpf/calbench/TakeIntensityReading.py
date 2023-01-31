import time
import ktl

from ddoitranslatormodule.KPFTranslatorFunction import KPFTranslatorFunction
from .. import (log, KPFException, FailedPreCondition, FailedPostCondition,
                FailedToReachDestination, check_input)


class TakeIntensityReading(KPFTranslatorFunction):
    '''
    '''
    @classmethod
    def pre_condition(cls, args, logger, cfg):
        return True

    @classmethod
    def perform(cls, args, logger, cfg):
        kpfcal = ktl.cache('kpfcal')
        intensemon = ktl.cache('kpflamps', 'INTENSEMON')

        # Turn on intensity monitor
        if intensemon.read() == 'Off':
            intensemon.write('On')
            boottime = cfg.get('times', 'intenmon_boot_time', fallback=5)
            time.sleep(boottime)

        # Verify serial connection is active
        if kpfcal['SERIALCONN'].read() == 'Off':
            kpfcal['SERIALCONN'].write('On')
            expr = f"($kpfcal.SERIALCONN == 'On')"
            boottime = cfg.get('times', 'intenmon_boot_time', fallback=5)
            success = ktl.waitFor(expr, timeout=boottime)
            if success is False:
                raise KPFException(f'Intensity monitor serial connection is Off')

        # Move sensor in to beam
        kpfcal['INTENMON'].write('Boresight')
        # Set averaging
        navg = cfg.get('times', 'intenmon_avg_time', fallback=60)
        kpfcal['NAVG'].write(navg)
        kpfcal['AVG'].write('On')

        # Check whether measuring is taking place
        expr = f"($kpfcal.MEASURING == 'Yes')"
        success = ktl.waitFor(expr, timeout=5)
        if success is False:
            raise KPFException(f'Intensity monitor is not measuring')

        # Wait for readings to be complete
        expr = f"($kpfcal.AVG == 'Off')"
        success = ktl.waitFor(expr, timeout=navg+10)
        if success is False:
            raise KPFException(f'Intensity monitor measurement timed out')

        # Move sensor out of beam
        kpfcal['INTENMON'].write('Out')

        # Turn off intensity monitor
        intensemon.write('Off')

    @classmethod
    def post_condition(cls, args, logger, cfg):
        return True
