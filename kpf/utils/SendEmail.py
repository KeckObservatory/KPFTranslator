import smtplib
from email.mime.text import MIMEText

from kpf import log, cfg
from kpf.exceptions import *
from kpf.KPFTranslatorFunction import KPFFunction, KPFScript


##-----------------------------------------------------------------------------
## SendEmail
##-----------------------------------------------------------------------------
class SendEmail(KPFFunction):
    '''Send an email

    Args:
        To (str): The email address to send the message to.
        From (str): The email address to use as the from address.
        Subject (str): Subject line for the email.
        Message (str): Message body of the email.
    '''
    @classmethod
    def pre_condition(cls, args):
        pass

    @classmethod
    def perform(cls, args):
        msg = MIMEText(args.get('Message', 'Test email. Please ignore.'))
        msg['To'] = args.get('To', 'kpf_info@keck.hawaii.edu')
        msg['From'] = args.get('From', 'kpf_info@keck.hawaii.edu')
        msg['Subject'] = args.get('Subject', 'KPF Alert')
        log.warning(f"Sending email, To {msg.get('To')}")
        log.warning(f"Sending email, Subject {msg.get('Subject')}")
        log.warning(f"{args.get('Message')}")
        s = smtplib.SMTP('relay.keck.hawaii.edu')
        s.send_message(msg)
        s.quit()

    @classmethod
    def post_condition(cls, args):
        pass
