import ktl

from kpf import log, cfg
from kpf.exceptions import *
from kpf.KPFTranslatorFunction import KPFFunction, KPFScript
from kpf.utils.SendEmail import SendEmail


##-------------------------------------------------------------------------
## CheckSoCalEnabled
##-------------------------------------------------------------------------
class CheckSoCalEnabled(KPFFunction):
    '''
    '''
    @classmethod
    def pre_condition(cls, args):
        pass

    @classmethod
    def perform(cls, args):
        CAN_OPEN = ktl.cache('kpfsocal', 'CAN_OPEN')
        if CAN_OPEN.read(binary=True) == True:
            print('CAN_OPEN is True')
        else:
            print('WARNING: CAN_OPEN is not True')
            try:
                msg = [f'KPF SoCal CAN_OPEN is not True',
                       f'',
                       f'SoCal is disabled.',
                       ]
                SendEmail.execute({'Subject': 'KPF SoCal CAN_OPEN is not True',
                                   'Message': '\n'.join(msg)})
            except Exception as email_err:
                log.error(f'Sending email failed')
                log.error(email_err)

    @classmethod
    def post_condition(cls, args):
        pass
