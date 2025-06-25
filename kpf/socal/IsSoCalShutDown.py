import ktl

from kpf.KPFTranslatorFunction import KPFTranslatorFunction
from kpf import (log, KPFException, FailedPreCondition, FailedPostCondition,
                 FailedToReachDestination, check_input)
from kpf.utils.SendEmail import SendEmail


class IsSoCalShutDown(KPFTranslatorFunction):
    '''Returns True if SoCal enclosure is closed and tracker is parked.

    ARGS:
    =====
    None
    '''
    @classmethod
    def pre_condition(cls, args, logger, cfg):
        pass

    @classmethod
    def perform(cls, args, logger, cfg):
        # Enclosure
        timeout = cfg.getfloat('SoCal', 'enclosure_status_time', fallback=10)
        ENCSTA = ktl.cache('kpfsocal', 'ENCSTA')
        is_closed = ENCSTA.waitFor("==1", timeout=timeout)

        EKOHOME = ktl.cache('kpfsocal', 'EKOHOME')
        is_home = EKOHOME.waitFor("==1", timeout=timeout)

        closedstr = {True: '', False: 'NOT '}[is_closed]
        parkedstr = {True: '', False: 'NOT '}[is_home]
        msg = f'SoCal is {closedstr}closed and {parkedstr}parked'
        print(msg)

        shutdown = is_closed and is_home
        if not shutdown and args.get('email', False) is True:
            try:
                SendEmail.execute({'Subject': f'KPF SoCal is not shut down properly',
                                   'Message': msg})
            except Exception as email_err:
                log.error(f'Sending email failed')
                log.error(email_err)

        return shutdown

    @classmethod
    def post_condition(cls, args, logger, cfg):
        pass

    @classmethod
    def add_cmdline_args(cls, parser, cfg=None):
        parser.add_argument('--email', dest="email",
                            default=False, action="store_true",
                            help='Send email if SoCal is not shut down?')

        return super().add_cmdline_args(parser, cfg)
