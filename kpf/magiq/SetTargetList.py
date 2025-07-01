from kpf import log, cfg
from kpf.exceptions import *
from kpf.KPFTranslatorFunction import KPFFunction, KPFScript
from kpf.telescope import KPF_is_selected_instrument
from kpf.magiq import magiq_server_command


class SetTargetList(KPFFunction):
    '''Given a list of OBs, generate a Keck Star List and send to MAGIQ.

    MAGIQ API documentation:
    http://suwebserver01.keck.hawaii.edu/magiqStatus/magiqServer.php
    '''
    @classmethod
    def pre_condition(cls, args):
        if not KPF_is_selected_instrument():
            raise KPFException('KPF is not selected instrument')

    @classmethod
    def perform(cls, args):
        params = {'targetlist': args.get('StarList')}
        nlines = len(args.get('StarList').split('\n'))
        log.info(f'Running Magiq setTargetList command with {nlines} lines')
        result = magiq_server_command('setTargetList', params=params, post=True)

    @classmethod
    def post_condition(cls, args):
        pass
