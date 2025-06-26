import ktl

def guider_is_ready():
    '''Checks that guider is powered on and some basic keywords are set.
    '''
    kpfguide = ktl.cache('kpfguide')
    kpfpower = ktl.cache('kpfpower')
    tests = [kpfpower['KPFGUIDE1'].read() == 'On',
             kpfguide['FPS'].read(binary=True) > 0,
             kpfguide['DISP1STA'].read() == 'Ready',
             kpfguide['DISP2STA'].read() == 'Ready',
             ]
    return np.all(np.array(tests))


def guider_is_active():
    '''Checks that the guide camera is taking exposures.
    '''
    CONTINUOUS = ktl.cache('kpfguide', 'CONTINUOUS').read()
    return CONTINUOUS.lower() == 'active'


def guider_is_saving():
    '''Checks that the guide camera is taking exposures and outputting stacked
    images as fits files.
    '''
    SAVE = ktl.cache('kpfguide', 'SAVE').read()
    return guider_is_active() and (SAVE.lower() == 'active')
