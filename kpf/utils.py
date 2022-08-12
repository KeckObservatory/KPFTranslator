import ktl

from . import log, KPFError

# Additional conditions to write:
# - Confirm FVCs are off

##-------------------------------------------------------------------------
## Pre- or Post- Conditions
##-------------------------------------------------------------------------
def check_guider_is_active():
    '''Checks that the guide camera is taking exposures.
    '''
    kpfguide = ktl.cache('kpfguide')
    continuous = kpfguide['CONTINUOUS'].read()
    return continuous.lower() == 'active'


def check_guider_is_saving():
    '''Checks that the guide camera is taking exposures and outputting stacked
    images as fits files.
    '''
    kpfguide = ktl.cache('kpfguide')
    save = kpfguide['SAVE'].read()
    return check_guider_is_active() and (save.lower() == 'yes')


def check_green_detector_power():
    kpfgreen = ktl.cache('kpfgreen')
    ccdpower = kpfgreen['CCDPOWER'].read()
    powersupply = kpfgreen['POWERSUPPLY'].read()
    if ccdpower in ['Intermediate', 'Standby']:
        log.warning(f"  Green detector: CCDPOWER = {ccdpower}")
    if ccdpower in ['Unknown', 'Off'] or powersupply == 'NotOK':
        msg = (f"Green detector: CCDPOWER = {ccdpower}, "
               f"POWERSUPPLY = {powersupply}")
        log.error(msg)
        return False
    return True


def check_red_detector_power():
    kpfred = ktl.cache('kpfgreen')
    ccdpower = kpfred['CCDPOWER'].read()
    powersupply = kpfred['POWERSUPPLY'].read()
    if ccdpower in ['Intermediate', 'Standby']:
        log.warning(f"  Red detector: CCDPOWER = {ccdpower}")
    if ccdpower in ['Unknown', 'Off'] or powersupply == 'NotOK':
        msg = (f"Red detector: CCDPOWER = {ccdpower}, "
               f"POWERSUPPLY = {powersupply}")
        log.error(msg)
        return False
    return True


def check_green_detector_temperature(temperature_tolerance=1):
    kpfgreen = ktl.cache('kpfgreen')
    current = kpfgreen['CURRTEMP'].read(binary=True)
    setpoint = kpfgreen['TEMPSET'].read(binary=True)
    diff = abs(current - setpoint)
    if diff > temperature_tolerance:
        msg = (f"Green detector temperature out of range: "
               f"{current:.1f} != {setpoint:.1f}")
        log.error(msg)
        return False
    else:
        log.info(f'Green detector temperature ok (diff={diff:.3f} C)')
        return True


def check_red_detector_temperature(temperature_tolerance=1):
    kpfred = ktl.cache('kpfred')
    current = kpfred['CURRTEMP'].read(binary=True)
    setpoint = kpfred['TEMPSET'].read(binary=True)
    diff = abs(current - setpoint)
    if diff > temperature_tolerance:
        msg = (f"Red detector temperature out of range: "
               f"{current:.1f} != {setpoint:.1f}")
        log.error(msg)
        return False
    else:
        log.info(f'Red detector temperature ok (diff={diff:.3f} C)')
        return True


def check_cahk_detector_temperature(temperature_tolerance=1):
    kpfhk = ktl.cache('kpf_hk')
    current = kpfhk['CURRTEMP'].read(binary=True)
    setpoint = kpfhk['COOLTARG'].read(binary=True)
    diff = abs(current - setpoint)
    if diff > temperature_tolerance:
        msg = (f"Ca H&K detector temperature out of range: "
               f"{current:.1f} C != {setpoint:.1f} C")
        log.error(msg)
        return False
    else:
        log.info(f'Ca H&K detector temperature ok (diff={diff:.3f} C)')
        return True
