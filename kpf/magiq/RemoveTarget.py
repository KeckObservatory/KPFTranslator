from kpf import log, cfg
from kpf.exceptions import *
from kpf.KPFTranslatorFunction import KPFFunction, KPFScript
from kpf.telescope import KPF_is_selected_instrument
from kpf.magiq import magiq_server_command
from kpf.magiq.GetTargetList import GetTargetList
from kpf.observatoryAPIs.GetTelescopeRelease import GetTelescopeRelease


class RemoveTarget(KPFFunction):
    '''Remove the specified target from the OA star list.

    MAGIQ API documentation:
    http://suwebserver01.keck.hawaii.edu/magiqStatus/magiqServer.php

    Args:
        TargetName (str): The name of the target to remove.

    Functions Called:

    - `kpf.observatoryAPIs.GetTelescopeRelease`
    '''
    @classmethod
    def pre_condition(cls, args):
        if not KPF_is_selected_instrument():
            raise KPFException('KPF is not selected instrument')
        if not GetTelescopeRelease.execute({}):
            raise KPFException('Telescope is not released')

    @classmethod
    def perform(cls, args):
        target_name = args.get('TargetName', None)
        params = {'target': target_name}
        log.info(f'Running Magiq removeTarget command {target_name}')
        result = magiq_server_command('removeTarget', params=params)

    @classmethod
    def post_condition(cls, args):
        pass

    @classmethod
    def add_cmdline_args(cls, parser):
        parser.add_argument('TargetName', type=str,
            help="Name of target to select")
        return super().add_cmdline_args(parser)


class RemoveAllTargets(KPFFunction):
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
        target_names, lines = GetTargetList.execute({})
        for target_name in target_names:
            params = {'target': target_name}
            result = magiq_server_command('removeTarget', params=params)

    @classmethod
    def post_condition(cls, args):
        pass

    @classmethod
    def add_cmdline_args(cls, parser):
        parser.add_argument('TargetName', type=str,
            help="Name of target to select")
        return super().add_cmdline_args(parser)
