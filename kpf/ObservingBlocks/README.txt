# KPF Observing Blocks (v2.0)

Observing blocks are represented as python dictionaries and consist of a subset of the following parts:
- Calibrations
- Target
- Observations
- Scheduling
- Metadata

Each of the above is a key for the dictionary.

## Calibrations

The calibrations element contains a list of dictionaries, each element of the list describes a single calibration.

## Target

The target element is a single dictionary containing the target information.

## Observations

The observations element contains a list of dictionaries, each element of the list describes a single on sky observation.

## Scheduling

The scheduling element is a single dictionary containing the scheduling information.  This is not used in OB execution.

## Metadata

The metadata element is a single dictionary containing miscellaneous information.  This is not used in OB execution.

# Types of OBs?

In this version of the KPF execution system, we are no longer explicitly setting an OB "type" (i.e. a `Template_Name` value).  OBs will be parsed to see which of the above entries they contain and all other dictionary keys will be ignored.  In the execution of an OB, only `Target`, `Calibrations`, and `Observations` are used.


If the OB contains `Target`:
- execute `SendTargetToMagiq`
    - ToDo: Set kpfconfig.TARGET_GMAG and TARGET_JMAG in `SendTargetToMagiq`

If the OB contains `Calibrations`:
- execute `ConfigureForCalibrations`
- loop over list of calibrations:
    - execute `ExecuteCal`
- execute `CleanupAfterCalibrations`
- Note: Combining `Calibrations` with a `Target` is not an intended mode, but the operational sequence here should be at least somewhat sensible.

If the OB contains `Target`:
- execute `SendTargetToMagiq`
    - ToDo: Set kpfconfig.TARGET_GMAG and TARGET_JMAG in `SendTargetToMagiq`
- execute `ConfigureForAcquisition`
    - This executes a slew cal if SLEWCALREQ is True
- execute `WaitForConfigureAcquisition`

If the OB contains `Observations`:
- execute `ConfigureForScience`
- loop over list of observations:
    - execute `ExecuteSci`
- execute `CleanupAfterScience`
