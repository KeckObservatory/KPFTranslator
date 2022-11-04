import numpy as np

import ktl


def get_fvc_outlet(camera='SCI'):
    '''Determines the outlet to control the specified FVC
    '''
    kpffvc = ktl.cache('kpffvc')
    return kpffvc[f"{camera}OUTLET"].read()


def fvc_is_ready(camera='SCI'):
    '''Checks that science FVC is powered up and in a standard configuration.
    '''
    outlet = get_fvc_outlet(camera=camera)
    kpffvc = ktl.cache('kpffvc')
    kpfpower = ktl.cache('kpfpower')
    tests = [kpfpower[f'{outlet}'].read() == 'On',
             kpffvc[f'{camera}AUTOEXP'].read() == 'Off',
             kpffvc[f'{camera}AUTOGAIN'].read() == 'Off',
             kpffvc[f'{camera}BLCLAMP'].read() == 'Disabled',
             abs(1.0-kpffvc[f'{camera}BLACKLEVEL'].read(binary=True)) < 0.001,
             kpffvc[f'{camera}GENABLE'].read() == 'Disabled',
             abs(1.0-kpffvc[f'{camera}GAMMA'].read(binary=True)) < 0.001,
             ]
    return np.all(np.array(tests))
