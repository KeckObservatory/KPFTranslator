import ktl

from .. import (KPFException, FailedPreCondition, FailedPostCondition,
                FailedToReachDestination, check_input)

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
        raise FailedPreCondition(f"Green detector: CCDPOWER = {ccdpower}")
    if ccdpower in ['Unknown', 'Off'] or powersupply == 'NotOK':
        msg = (f"Green detector: CCDPOWER = {ccdpower}, "
               f"POWERSUPPLY = {powersupply}")
        raise FailedPreCondition(msg)


def red_detector_power_is_on():
    '''Checks that the camera power is on
    '''
    kpfred = ktl.cache('kpfgreen')
    ccdpower = kpfred['CCDPOWER'].read()
    powersupply = kpfred['POWERSUPPLY'].read()
    if ccdpower in ['Intermediate', 'Standby']:
        raise FailedPreCondition(f"Red detector: CCDPOWER = {ccdpower}")
    if ccdpower in ['Unknown', 'Off'] or powersupply == 'NotOK':
        msg = (f"Red detector: CCDPOWER = {ccdpower}, "
               f"POWERSUPPLY = {powersupply}")
        raise FailedPreCondition(msg)


def green_detector_temperature_is_ok(temperature_tolerance=10):
    '''Checks that the camera temperature is near setpoint
    '''
    kpfgreen = ktl.cache('kpfgreen')
    current = kpfgreen['CURRTEMP'].read(binary=True)
    setpoint = kpfgreen['TEMPSET'].read(binary=True)
    diff = abs(current - setpoint)
    if diff > temperature_tolerance:
        msg = (f"Green detector temperature out of range: "
               f"{current:.1f} != {setpoint:.1f}")
        raise FailedPreCondition(msg)


def red_detector_temperature_is_ok(temperature_tolerance=10):
    '''Checks that the camera temperature is near setpoint
    '''
    kpfred = ktl.cache('kpfred')
    current = kpfred['CURRTEMP'].read(binary=True)
    setpoint = kpfred['TEMPSET'].read(binary=True)
    diff = abs(current - setpoint)
    if diff > temperature_tolerance:
        msg = (f"Red detector temperature out of range: "
               f"{current:.1f} != {setpoint:.1f}")
        raise FailedPreCondition(msg)


def cahk_detector_temperature_is_ok(temperature_tolerance=10):
    '''Checks that the camera temperature is near setpoint
    '''
    kpfhk = ktl.cache('kpf_hk')
    current = kpfhk['CURRTEMP'].read(binary=True)
    setpoint = kpfhk['COOLTARG'].read(binary=True)
    diff = abs(current - setpoint)
    if diff > temperature_tolerance:
        msg = (f"Ca H&K detector temperature out of range: "
               f"{current:.1f} C != {setpoint:.1f} C")
        raise FailedPreCondition(msg)
