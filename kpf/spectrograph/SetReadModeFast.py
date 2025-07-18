from pathlib import Path
import time
import ktl

from kpf import log, cfg
from kpf.exceptions import *
from kpf.KPFTranslatorFunction import KPFFunction, KPFScript
from kpf.spectrograph.QueryReadMode import QueryReadMode
from kpf.utils.SendEmail import SendEmail


class SetReadModeFast(KPFFunction):
    '''Configure both detectors to fast read mode by changing the ACF files
    they are using.

    ARGS:
    =====
    None
    '''
    @classmethod
    def pre_condition(cls, args):
        pass

    @classmethod
    def perform(cls, args):
        green_mode, red_mode = QueryReadMode.execute({})
        if green_mode != 'fast':
            msg = f'Setting Green CCD read mode fast'
            log.info(msg)
            # Email to kpf_info
            try:
                SendEmail.execute({'Subject': msg, 'Message': msg})
            except Exception as email_err:
                log.error(f'Sending email failed')
                log.error(email_err)
            kpfgreen = ktl.cache('kpfgreen')
            green_fast_file = cfg.get('acf_files', 'green_fast')
            green_ACFFILE = Path(kpfgreen['ACFFILE'].read()).stem
            if green_ACFFILE != green_fast_file:
                kpfgreen['ACF'].write(green_fast_file)
            time.sleep(1)
        if red_mode != 'fast':
            msg = f'Setting Red CCD read mode fast'
            log.info(msg)
            # Email to kpf_info
            try:
                SendEmail.execute({'Subject': msg, 'Message': msg})
            except Exception as email_err:
                log.error(f'Sending email failed')
                log.error(email_err)
            kpfred = ktl.cache('kpfred')
            red_fast_file = cfg.get('acf_files', 'red_fast')
            red_ACFFILE = Path(kpfred['ACFFILE'].read()).stem
            if red_ACFFILE != red_fast_file:
                kpfred['ACF'].write(red_fast_file)
            time.sleep(1)

    @classmethod
    def post_condition(cls, args):
        green_mode, red_mode = QueryReadMode.execute({})
        if green_mode != "fast":
            raise FailedToReachDestination(green_mode, "fast")
        if red_mode != "fast":
            raise FailedToReachDestination(red_mode, "fast")
