from kpf import log, cfg
from kpf.exceptions import *
from kpf.KPFTranslatorFunction import KPFFunction, KPFScript
from kpf.telescope import KPF_is_selected_instrument
from kpf.magiq import magiq_server_command
from kpf.schedule.GetTelescopeRelease import GetTelescopeRelease


class AddTarget(KPFFunction):
    '''

    MAGIQ API documentation:
    http://suwebserver01.keck.hawaii.edu/magiqStatus/magiqServer.php
    '''
    @classmethod
    def pre_condition(cls, args):
        if not KPF_is_selected_instrument():
            raise KPFException('KPF is not selected instrument')
        if not GetTelescopeRelease.execute({}):
            raise KPFException('Telescope is not released')

    @classmethod
    def perform(cls, args):
#         target=Target&ra=12:34:56&dec=11:22:33&frame=2000&options=a=1 b=2 c=3
        params = {'target': args.get('TargetName'),
                  'ra': args.get('RA'),
                  'dec': args.get('Dec'),
                  'frame': '2000' if args.get('Equinox') == 'J2000' else args.get('Equinox'),
                  'options': '',
                  }
        if abs(args.get('DRA')) > 0.001:
            params['options'] += f"DRA={args.get('DRA')}"
        if abs(args.get('DDEC')) > 0.001:
            params['options'] += f"DRA={args.get('DDEC')}"
        log.info(f'Running Magiq addTarget command {params.get("target")}')
        result = magiq_server_command('addTarget', params=params)


    @classmethod
    def post_condition(cls, args):
        pass
