import requests

import ktl

from kpf import cfg


def KPF_is_selected_instrument():
    dcsint = cfg.getint('telescope', 'telnr', fallback=1)
    INSTRUME = ktl.cache(f'dcs{dcsint}', 'INSTRUME').read()
    return INSTRUME in ['KPF', 'KPF-CC']


def magiq_server_command(command, params=None):
    dcsint = cfg.getint('telescope', 'telnr', fallback=1)
    url = cfg.get('telescope', 'magiq_server')
    url = url.replace('kN', f'k{dcsint:1d}')
    if not KPF_is_selected_instrument() and command != 'getTargetlist':
        print('KPF is not selected instrument')
        return None
    if params is not None:
        for i,key in enumerate(params.keys()):
            if i == 0:
                command += '?'
            else:
                command += '&'
            command += f"{key}={params[key]}"
    print(f"Running: {url}{command}")
    r = requests.get(f"{url}{command}")
    return r.text
