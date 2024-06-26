import smtplib
from email.mime.text import MIMEText

from kpf.KPFTranslatorFunction import KPFTranslatorFunction
from kpf import (log, KPFException, FailedPreCondition, FailedPostCondition,
                 FailedToReachDestination, check_input)


##-----------------------------------------------------------------------------
## SendEmail
##-----------------------------------------------------------------------------
class SendEmail(KPFTranslatorFunction):
    '''Send an email

    ARGS:
    =====
    :To: `str` The email address to send the message to.
    :From: `str` The email address to use as the from address.
    :Subject: `str` Subject line for the email.
    :Message: `str` Message body of the email.
    '''
    @classmethod
    def pre_condition(cls, args, logger, cfg):
        pass

    @classmethod
    def perform(cls, args, logger, cfg):
        msg = MIMEText(args.get('Message', 'Test email. Please ignore.'))
        msg['To'] = args.get('To', 'kpf_info@keck.hawaii.edu')
        msg['From'] = args.get('From', 'kpf_info@keck.hawaii.edu')
        msg['Subject'] = args.get('Subject', 'KPF Alert')
        log.warning(f"Sending email, To {msg['To']}")
        log.warning(f"Sending email, Subject {msg['Subject']}")
        log.warning(f"{msg['Message']}")
        s = smtplib.SMTP('relay.keck.hawaii.edu')
        s.send_message(msg)
        s.quit()

    @classmethod
    def post_condition(cls, args, logger, cfg):
        pass
