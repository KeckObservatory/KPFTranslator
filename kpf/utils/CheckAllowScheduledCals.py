import ktl

from kpf import log, cfg
from kpf.exceptions import *
from kpf.KPFTranslatorFunction import KPFFunction, KPFScript
from kpf.utils.SendEmail import SendEmail


##-------------------------------------------------------------------------
## CheckAllowScheduledCals
##-------------------------------------------------------------------------
class CheckAllowScheduledCals(KPFFunction):
    '''
    '''
    @classmethod
    def pre_condition(cls, args):
        pass

    @classmethod
    def perform(cls, args):
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
    def post_condition(cls, args):
        pass
