import requests

from kpf import log, cfg


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
    if post:
        log.debug(f"Post to Magiq: {url}{command}")
        r = requests.post(f"{url}{command}")
    else:
#         command = command.replace('+', '%2B')
#         command = command.replace(' ', '%20')
#         command = command.replace('#', '%23')
        log.debug(f"Get from Magiq: {url}{command}")
        r = requests.get(f"{url}{command}")
    result = r.text.strip().strip('\n')
    log.debug(f"Response from Magiq: {result}")
    return result
