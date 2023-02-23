import smtplib
from email.mime.text import MIMEText

from kpf.KPFTranslatorFunction import KPFTranslatorFunction
from .. import (log, KPFException, FailedPreCondition, FailedPostCondition,
                FailedToReachDestination, check_input)

##-----------------------------------------------------------------------------
## SetObserverFromSchedule
##-----------------------------------------------------------------------------
class SendEmail(KPFTranslatorFunction):
    '''Send an email
    '''
    @classmethod
    def pre_condition(cls, args, logger, cfg):
        check_input(args, 'Message')
        check_input(args, 'Subject')
        return True

    @classmethod
    def perform(cls, args, logger, cfg):
        msg = MIMEText(args.get('Message'))
        msg['Subject'] = args.get('Subject', 'KPF Alert')
        msg['To'] = args.get('To', 'kpf_info@keck.hawaii.edu')
        msg['From'] = args.get('From', 'kpf_info@keck.hawaii.edu')
        log.warning(f"Sending email, To {msg['To']}")
        log.warning(f"Sending email, Subject {msg['Subject']}")
        log.warning(f"{args.get('message')}")
        s = smtplib.SMTP('localhost')
        s.send_message(msg)
        s.quit()

    @classmethod
    def post_condition(cls, args, logger, cfg):
        pass
