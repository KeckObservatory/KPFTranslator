import ktl

from kpf import log, cfg
from kpf.exceptions import *
from kpf.KPFTranslatorFunction import KPFFunction, KPFScript
from kpf.telescope import KPF_is_selected_instrument


class SelectTarget(KPFFunction):
    '''

    MAGIQ API documentation:
    http://suwebserver01.keck.hawaii.edu/magiqStatus/magiqServer.php
    '''
    @classmethod
    def pre_condition(cls, args):
        pass

    @classmethod
    def perform(cls, args):
        params = {'Target': args.get('TargetName', None)}
        result = magiq_server_command('getTargetlist', params=params)

    @classmethod
    def post_condition(cls, args):
        pass
