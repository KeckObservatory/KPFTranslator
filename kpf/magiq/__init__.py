import requests

from kpf import cfg


def magiq_server_command(command, params=None, post=False):
    dcsint = cfg.getint('telescope', 'telnr', fallback=1)
    url = cfg.get('telescope', 'magiq_server')
    url = url.replace('kN', f'k{dcsint:1d}')
    if params is not None:
        for i,key in enumerate(params.keys()):
            if i == 0:
                command += '?'
            else:
                command += '&'
            command += f"{key}={params[key]}"
#     print(f"Running: {url}{command}")
    if post:
        r = requests.post(f"{url}{command}")
    else:
        r = requests.get(f"{url}{command}")
    return r.text
