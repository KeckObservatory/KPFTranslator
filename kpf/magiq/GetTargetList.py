import requests

from kpf import log, cfg
from kpf.exceptions import *
from kpf.KPFTranslatorFunction import KPFFunction, KPFScript
from kpf.magiq import magiq_server_command


class GetTargetList(KPFFunction):
    '''

    MAGIQ API documentation:
    http://suwebserver01.keck.hawaii.edu/magiqStatus/magiqServer.php
    '''
    @classmethod
    def pre_condition(cls, args):
        pass

    @classmethod
    def perform(cls, args):
        log.info(f'Running Magiq getTargetlist command')
        result = magiq_server_command('getTargetlist')
        lines = result.split('\n')
        target_names = [line[:16].strip() for line in lines]
        return target_names, lines

    @classmethod
    def post_condition(cls, args):
        pass
