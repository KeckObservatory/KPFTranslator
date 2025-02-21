import ktl

from kpf.KPFTranslatorFunction import KPFTranslatorFunction
from kpf import (log, KPFException, FailedPreCondition, FailedPostCondition,
                 FailedToReachDestination, check_input)
from kpf.utils.SendEmail import SendEmail


##-------------------------------------------------------------------------
## CheckAllowScheduledCals
##-------------------------------------------------------------------------
class CheckAllowScheduledCals(KPFTranslatorFunction):
    '''
    '''
    @classmethod
    def pre_condition(cls, args, logger, cfg):
        pass

    @classmethod
    def perform(cls, args, logger, cfg):
        ALLOWSCHEDULEDCALS = ktl.cache('kpfconfig', 'ALLOWSCHEDULEDCALS')
        if ALLOWSCHEDULEDCALS.read() == 'Yes':
            print('ALLOWSCHEDULEDCALS is "Yes"')
        else:
            print('WARNING: ALLOWSCHEDULEDCALS is not "Yes"')
            try:
                msg = [f'KPF ALLOWSCHEDULEDCALS is not "Yes"',
                       f'',
                       f'End of Night script may not have been run properly',
                       ]
                SendEmail.execute({'Subject': 'KPF ALLOWSCHEDULEDCALS is not "Yes"',
                                   'Message': '\n'.join(msg)})
            except Exception as email_err:
                log.error(f'Sending email failed')
                log.error(email_err)

    @classmethod
    def post_condition(cls, args, logger, cfg):
        pass
