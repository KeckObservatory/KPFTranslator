import requests

from kpf import log, cfg
from kpf.exceptions import *
from kpf.KPFTranslatorFunction import KPFFunction, KPFScript
from kpf.telescope import KPF_is_selected_instrument, magiq_server_command


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
        result = magiq_server_command('getTargetlist')
        print(result)

    @classmethod
    def post_condition(cls, args):
        pass
