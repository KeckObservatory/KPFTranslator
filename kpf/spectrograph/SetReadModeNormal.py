from pathlib import Path
import time
import ktl

from kpf import log, cfg
from kpf.exceptions import *
from kpf.KPFTranslatorFunction import KPFFunction, KPFScript
from kpf.spectrograph.QueryReadMode import QueryReadMode


class SetReadModeNormal(KPFFunction):
    '''Configure both detectors to normal read mode by changing the ACF files
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
        if green_mode != 'normal':
            msg = f'Setting Green CCD read mode normal'
            log.info(msg)
            # Email to kpf_info
            try:
                SendEmail.execute({'Subject': msg, 'Message': msg})
            except Exception as email_err:
                log.error(f'Sending email failed')
                log.error(email_err)
            kpfgreen = ktl.cache('kpfgreen')
            green_normal_file = cfg.get('acf_files', 'green_normal')
            green_ACFFILE = Path(kpfgreen['ACFFILE'].read()).stem
            if green_ACFFILE != green_normal_file:
                kpfgreen['ACF'].write(green_normal_file)
            time.sleep(1)
        if red_mode != 'normal':
            msg = f'Setting Red CCD read mode normal'
            log.info(msg)
            # Email to kpf_info
            try:
                SendEmail.execute({'Subject': msg, 'Message': msg})
            except Exception as email_err:
                log.error(f'Sending email failed')
                log.error(email_err)
            kpfred = ktl.cache('kpfred')
            red_normal_file = cfg.get('acf_files', 'red_normal')
            red_ACFFILE = Path(kpfred['ACFFILE'].read()).stem
            if red_ACFFILE != red_normal_file:
                kpfred['ACF'].write(red_normal_file)
            time.sleep(1)

    @classmethod
    def post_condition(cls, args):
        if QueryFastReadMode.execute({}) != False:
            raise FailedPostCondition(f"Read mode change failed")
