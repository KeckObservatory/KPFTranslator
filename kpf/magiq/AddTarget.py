from kpf import log, cfg
from kpf.exceptions import *
from kpf.KPFTranslatorFunction import KPFFunction, KPFScript
from kpf.telescope import KPF_is_selected_instrument


class AddTarget(KPFFunction):
    '''

    MAGIQ API documentation:
    http://suwebserver01.keck.hawaii.edu/magiqStatus/magiqServer.php
    '''
    @classmethod
    def pre_condition(cls, args):
        if not KPF_is_selected_instrument():
            raise KPFException('KPF is not selected instrument')

    @classmethod
    def perform(cls, args):
        pass

    @classmethod
    def post_condition(cls, args):
        pass
