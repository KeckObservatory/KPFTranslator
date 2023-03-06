import time

import ktl

from ddoitranslatormodule.KPFTranslatorFunction import KPFTranslatorFunction
from .. import (log, KPFException, FailedPreCondition, FailedPostCondition,
                FailedToReachDestination, check_input)
from .SendEmail import SendEmail


##-------------------------------------------------------------------------
## TriggerGreenMiniFill
##-------------------------------------------------------------------------
class TriggerGreenMiniFill(KPFTranslatorFunction):
    '''I really hope this is not necessary in the long term.
    '''
    @classmethod
    def pre_condition(cls, args, logger, cfg):
        kpffill = ktl.cache('kpffill')
        if kpffill['GREENFILLIP'].read() == 'True':
            raise FailedPreCondition('Green fill already in progress')
        return True

    @classmethod
    def perform(cls, args, logger, cfg):
        kpffill = ktl.cache('kpffill')
        # Start fill
        log.warning(f'Starting green mini fill')
        kpffill['GREENSTART'].write(1)
        # Wait
        sleep_time = 240
        log.debug(f'Sleeping {sleep_time:.0f} s')
        time.sleep(sleep_time)
        # Stop fill
        if kpffill['GREENFILLIP'].read() == 'True':
            log.warning(f'Stopping green mini fill')
            kpffill['GREENSTOP'].write(1)
            time.sleep(5)
        else:
            msg = 'Expected green mini fill to be in progress.'
            SendEmail.execute({'Subject': 'TriggerGreenMiniFill Failed',
                               'Message': f'{msg}'})
            raise KPFException(msg)

    @classmethod
    def post_condition(cls, args, logger, cfg):
        kpffill = ktl.cache('kpffill')
        if kpffill['GREENFILLIP'].read() == 'True':
            msg = 'Green still in progress, should be stopped!'
            SendEmail.execute({'Subject': 'TriggerGreenMiniFill Failed',
                               'Message': f'{msg}'})
            raise FailedPostCondition(msg)
        return True
