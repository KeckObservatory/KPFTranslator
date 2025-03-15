import ktl

from kpf import log, cfg
from kpf.exceptions import *
from kpf.KPFTranslatorFunction import KPFFunction, KPFScript
from kpf.telescope import KPF_is_selected_instrument


class SetTargetList(KPFFunction):
    '''Given a list of OBs, generate a Keck Star List and send to MAGIQ.

    MAGIQ API documentation:
    http://suwebserver01.keck.hawaii.edu/magiqStatus/magiqServer.php
    '''
    @classmethod
    def pre_condition(cls, args):
        pass

    @classmethod
    def perform(cls, args):


    @classmethod
    def post_condition(cls, args):
        pass
