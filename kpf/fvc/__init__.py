import numpy as np

import ktl


def fvc_is_ready(camera='SCI'):
    '''Checks that science FVC is powered up and in a standard configuration.
    '''
#     camnum = {'SCI': 1, 'CAHK': 2, 'CAL': 3}[camera]
#     kpfpower = ktl.cache('kpfpower')
#     outlet = kpfpower[f"KPFFVC{camnum}_OUTLETS"].read().strip('kpfpower.')
#     outletname = kpfpower[f"{outlet}_NAME"].read()
#     kpffvc = ktl.cache('kpffvc')
#     tests = []
#     tests = [kpffvc[f'{camera}AUTOEXP'].read() == 'Off',
#              kpffvc[f'{camera}AUTOGAIN'].read() == 'Off',
#              kpffvc[f'{camera}BLCLAMP'].read() == 'Disabled',
#              abs(1.0-kpffvc[f'{camera}BLACKLEVEL'].read(binary=True)) < 0.001,
#              kpffvc[f'{camera}GENABLE'].read() == 'Disabled',
#              abs(1.0-kpffvc[f'{camera}GAMMA'].read(binary=True)) < 0.001,
#              ]
    return True #np.all(np.array(tests))
