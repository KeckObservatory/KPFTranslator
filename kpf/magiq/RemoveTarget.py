from kpf import log, cfg
from kpf.exceptions import *
from kpf.KPFTranslatorFunction import KPFFunction, KPFScript
from kpf.telescope import KPF_is_selected_instrument
from kpf.magiq import magiq_server_command


class RemoveTarget(KPFFunction):
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
        params = {'Target': args.get('TargetName', None)}
        result = magiq_server_command('selectTarget', params=params)

    @classmethod
    def post_condition(cls, args):
        pass

    @classmethod
    def add_cmdline_args(cls, parser):
        parser.add_argument('TargetName', type=str,
            help="Name of target to select")
        return super().add_cmdline_args(parser)
