from kpf import log, cfg
from kpf.exceptions import *
from kpf.KPFTranslatorFunction import KPFFunction, KPFScript
from kpf.telescope import KPF_is_selected_instrument
from kpf.magiq import magiq_server_command
from kpf.magiq.GetTargetList import GetTargetList


class SelectTarget(KPFFunction):
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
        target_name = args.get('TargetName', None)
        target_names, lines = GetTargetList.execute({})
        if target_name in target_names:
            log.info(f'Selecting {target_name} in Magiq')
            params = {'target': target_name}
            log.info(f'Running Magiq selectTarget command {target_name}')
            result = magiq_server_command('selectTarget', params=params)
        else:
            log.error(f'Target name "{target_name}" not in current Magiq list')
            log.debug(target_names)

    @classmethod
    def post_condition(cls, args):
        pass

    @classmethod
    def add_cmdline_args(cls, parser):
        parser.add_argument('TargetName', type=str,
            help="Name of target to select")
        return super().add_cmdline_args(parser)
