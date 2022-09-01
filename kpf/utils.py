import ktl

KPFError = Exception


# Additional conditions to write:
# - Confirm FVCs are off

##-------------------------------------------------------------------------
## Pre- or Post- Conditions
##-------------------------------------------------------------------------
def fiu_hatch_is_open():
    '''Verifies that FIU hatch is open
    '''
    kpffiu = ktl.cache('kpffiu')
    return kpffiu['HATCH'].read() == 'Open'


def fiu_hatch_is_closed():
    '''Verifies that FIU hatch is closed
    '''
    kpffiu = ktl.cache('kpffiu')
    return kpffiu['HATCH'].read() == 'Closed'


def guider_is_active():
    '''Checks that the guide camera is taking exposures.
    '''
    kpfguide = ktl.cache('kpfguide')
    continuous = kpfguide['CONTINUOUS'].read()
    return continuous.lower() == 'active'


def guider_is_saving():
    '''Checks that the guide camera is taking exposures and outputting stacked
    images as fits files.
    '''
    kpfguide = ktl.cache('kpfguide')
    save = kpfguide['SAVE'].read()
    return guider_is_active() and (save.lower() == 'active')


def green_detector_power_is_on():
    '''Checks that the camera power is on
    '''
    kpfgreen = ktl.cache('kpfgreen')
    ccdpower = kpfgreen['CCDPOWER'].read()
    powersupply = kpfgreen['POWERSUPPLY'].read()
    if ccdpower in ['Intermediate', 'Standby']:
        print(f"  Green detector: CCDPOWER = {ccdpower}")
    if ccdpower in ['Unknown', 'Off'] or powersupply == 'NotOK':
        msg = (f"Green detector: CCDPOWER = {ccdpower}, "
               f"POWERSUPPLY = {powersupply}")
        print(msg)
        return False
    return True


def red_detector_power_is_on():
    '''Checks that the camera power is on
    '''
    kpfred = ktl.cache('kpfgreen')
    ccdpower = kpfred['CCDPOWER'].read()
    powersupply = kpfred['POWERSUPPLY'].read()
    if ccdpower in ['Intermediate', 'Standby']:
        print(f"  Red detector: CCDPOWER = {ccdpower}")
    if ccdpower in ['Unknown', 'Off'] or powersupply == 'NotOK':
        msg = (f"Red detector: CCDPOWER = {ccdpower}, "
               f"POWERSUPPLY = {powersupply}")
        print(msg)
        return False
    return True


def green_detector_temperature_is_ok(temperature_tolerance=1):
    '''Checks that the camera temperature is near setpoint
    '''
    kpfgreen = ktl.cache('kpfgreen')
    current = kpfgreen['CURRTEMP'].read(binary=True)
    setpoint = kpfgreen['TEMPSET'].read(binary=True)
    diff = abs(current - setpoint)
    if diff > temperature_tolerance:
        msg = (f"Green detector temperature out of range: "
               f"{current:.1f} != {setpoint:.1f}")
        print(msg)
        return False
    else:
        print(f'Green detector temperature ok (diff={diff:.3f} C)')
        return True


def red_detector_temperature_is_ok(temperature_tolerance=1):
    '''Checks that the camera temperature is near setpoint
    '''
    kpfred = ktl.cache('kpfred')
    current = kpfred['CURRTEMP'].read(binary=True)
    setpoint = kpfred['TEMPSET'].read(binary=True)
    diff = abs(current - setpoint)
    if diff > temperature_tolerance:
        msg = (f"Red detector temperature out of range: "
               f"{current:.1f} != {setpoint:.1f}")
        print(msg)
        return False
    else:
        print(f'Red detector temperature ok (diff={diff:.3f} C)')
        return True


def cahk_detector_temperature_is_ok(temperature_tolerance=1):
    '''Checks that the camera temperature is near setpoint
    '''
    kpfhk = ktl.cache('kpf_hk')
    current = kpfhk['CURRTEMP'].read(binary=True)
    setpoint = kpfhk['COOLTARG'].read(binary=True)
    diff = abs(current - setpoint)
    if diff > temperature_tolerance:
        msg = (f"Ca H&K detector temperature out of range: "
               f"{current:.1f} C != {setpoint:.1f} C")
        print(msg)
        return False
    else:
        print(f'Ca H&K detector temperature ok (diff={diff:.3f} C)')
        return True
