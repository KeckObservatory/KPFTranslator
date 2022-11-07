import ktl

from .. import log

##-------------------------------------------------------------------------
## Pre- or Post- Conditions
##-------------------------------------------------------------------------
def green_detector_power_is_on():
    '''Checks that the camera power is on
    '''
    kpfgreen = ktl.cache('kpfgreen')
    ccdpower = kpfgreen['CCDPOWER'].read()
    powersupply = kpfgreen['POWERSUPPLY'].read()
    if ccdpower in ['Intermediate', 'Standby']:
        log.error(f"  Green detector: CCDPOWER = {ccdpower}")
    if ccdpower in ['Unknown', 'Off'] or powersupply == 'NotOK':
        msg = (f"Green detector: CCDPOWER = {ccdpower}, "
               f"POWERSUPPLY = {powersupply}")
        log.error(msg)
        return False
    return True


def red_detector_power_is_on():
    '''Checks that the camera power is on
    '''
    kpfred = ktl.cache('kpfgreen')
    ccdpower = kpfred['CCDPOWER'].read()
    powersupply = kpfred['POWERSUPPLY'].read()
    if ccdpower in ['Intermediate', 'Standby']:
        log.error(f"  Red detector: CCDPOWER = {ccdpower}")
    if ccdpower in ['Unknown', 'Off'] or powersupply == 'NotOK':
        msg = (f"Red detector: CCDPOWER = {ccdpower}, "
               f"POWERSUPPLY = {powersupply}")
        log.error(msg)
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
        log.error(msg)
        return False
    else:
        log.debug(f'Green detector temperature ok (diff={diff:.3f} C)')
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
        log.error(msg)
        return False
    else:
        log.debug(f'Red detector temperature ok (diff={diff:.3f} C)')
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
        log.error(msg)
        return False
    else:
        log.debug(f'Ca H&K detector temperature ok (diff={diff:.3f} C)')
        return True
