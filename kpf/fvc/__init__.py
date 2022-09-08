import ktl


def fvc_is_ready(camera='SCI'):
    '''Checks that science FVC is powered up and in a standard configuration.
    '''
    outlet = {'SCI': 'K5',
              'CAHK': 'K6',
              'CAL': 'F6'}
    kpffvc = ktl.cache('kpffvc')
    kpfpower = ktl.cache('kpfpower')
    tests = [kpfpower[f'OUTLET_{outlet}'].read() == 'On',
             kpffvc[f'{camera}AUTOEXP'].read() > 'Off',
             kpffvc[f'{camera}AUTOGAIN'].read() > 'Off',
             kpffvc[f'{camera}BLCLAMP'].read() > 'Disabled',
             abs(1.0-kpffvc[f'{camera}BLACKLEVEL'].read(binary=True)) < 0.001,
             kpffvc[f'{camera}GENABLE'].read() > 'Disabled',
             abs(1.0-kpffvc[f'{camera}GAMMA'].read(binary=True)) < 0.001,
             ]
    return np.all(np.array(tests))


def sci_fvc_is_ready():
    fvc_is_ready(camera='SCI')


def cahk_fvc_is_ready():
    fvc_is_ready(camera='CAHK')


def cal_fvc_is_ready():
    fvc_is_ready(camera='CAL')
