import smtplib
from email.mime.text import MIMEText

from kpf.KPFTranslatorFunction import KPFTranslatorFunction
from .. import log


##-----------------------------------------------------------------------------
## SendEmail
##-----------------------------------------------------------------------------
class SendEmail(KPFTranslatorFunction):
    '''Send an email
    '''
    @classmethod
    def pre_condition(cls, args, logger, cfg):
        return True

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
