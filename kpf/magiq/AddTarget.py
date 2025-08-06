from kpf import log, cfg
from kpf.exceptions import *
from kpf.KPFTranslatorFunction import KPFFunction, KPFScript
from kpf.telescope import KPF_is_selected_instrument
from kpf.magiq import magiq_server_command
from kpf.observatoryAPIs.GetTelescopeRelease import GetTelescopeRelease


class AddTarget(KPFFunction):
    '''Add the specified target to the OA star list.

    MAGIQ API documentation:
    http://suwebserver01.keck.hawaii.edu/magiqStatus/magiqServer.php

    Args:
        TargetName (str): The name of the target to add.
        ra (str): The right ascension of the target.
        dec (str): The declination of the target.
        frame (str): The frame (e.g. J2000)
        DRA (float): The RA differential tracking rate (as per the keck star
                     list documentation) [optional].
        DDEC (float): The DEC differential tracking rate (as per the keck star
                      list documentation) [optional].
        options (str): The option string as documented in the Magiq API.

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
#         target=Target&ra=12:34:56&dec=11:22:33&frame=2000&options=a=1 b=2 c=3
        params = {'target': args.get('TargetName'),
                  'ra': args.get('RA'),
                  'dec': args.get('Dec'),
                  'frame': '2000' if args.get('Equinox') == 'J2000' else args.get('Equinox'),
                  'options': '',
                  }
        if abs(args.get('DRA', 0)) > 0.001:
            params['options'] += f"DRA={args.get('DRA')}"
        if abs(args.get('DDEC', 0)) > 0.001:
            params['options'] += f"DRA={args.get('DDEC')}"
        log.info(f'Running Magiq addTarget command {params.get("target")}')
        result = magiq_server_command('addTarget', params=params)


    @classmethod
    def post_condition(cls, args):
        pass
