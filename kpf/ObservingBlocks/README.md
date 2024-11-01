# KPF Observing Blocks (v2.0)

## Components

Observing blocks consist of some subset of the following parts:
- Metadata describing the OB
- Calibrations
- Target
- Observations
- ScheduleData

### Metadata

The metadata consists of a few key-value pairs. It is not used in OB execution.

### Calibrations

The calibrations element contains a list of dictionaries, each element of the list describes a single calibration.

### Target

The target element is a single dictionary containing the target information.

### Observations

The observations element contains a list of dictionaries, each element of the list describes a single on sky observation.

### ScheduleData

The schedule data element is a single dictionary containing the scheduling information.  This is not used in OB execution.

## Types of OBs?

In this version of the KPF execution system, we are no longer explicitly setting an OB "type" (i.e. a `Template_Name` value).  OBs will be parsed to see which of the above entries they contain and will be executed appropriately.  In the execution of an OB, only `Target`, `Calibrations`, and `Observations` are used.

## Outline of Execution Logic

If the OB contains `Target`:
- execute `SendTargetToMagiq`

If the OB contains `Calibrations`:
- execute `ConfigureForCalibrations`
- loop over list of calibrations:
    - execute `ExecuteCal`
- execute `CleanupAfterCalibrations`
- Note: Combining `Calibrations` with a `Target` is not an intended mode, but the operational sequence here should be at least somewhat sensible.

If the OB contains `Target`:
- execute `ConfigureForAcquisition`
    - This executes a slew cal if SLEWCALREQ is True
- execute `WaitForConfigureAcquisition`

If the OB contains `Observations`:
- execute `ConfigureForScience`
- loop over list of observations:
    - execute `ExecuteSci`
- execute `CleanupAfterScience`


# KPF Database

The OBs for KPF will be stored in a database for Community Cadence (KPF-CC) operations.  The sections below describe tables in that database most tables correspond to one of the OB elements above.

## ObservingBlock

* ProgramID: string
* AssociatedPrograms: string
* CommentToObserver: string
* Schedule: Points to 0 or 1 instances of ScheduleData
* Target: Points to 0 or 1 instances of Target
* Observations: Points to 0 or more instances of Observation (order within the list must be maintained)
* Calibrations: Points to 0 or more instances of Calibration (order within the list must be maintained)

Notes:
- The above describes a fully featured KPF OB.  KPF-CC OBs are a special case.
- KPF-CC OBs built by the web form will include only a single instance of
Observation.
- Multiple Observations in a single OB are a special case we should support via
the API, but not the web form.
- The Schedule component is optional for classical programs.
- Calibrations will not be part of the web form, but I want to be able to store
them in the DB for use in other contexts.


## ScheduleData

See ScheduleDataProperties.yaml


## Target

See TargetProperties.yaml


## Observation

See ObservationProperties.yaml


## Calibration

See CalibrationProperties.yaml


## ExecutionHistory

* OB Unique ID: 
* Timestamp: timestamp
* Exposures: list of floats


## ExecutionComments

* OB Unique ID: 
* Timestamp: timestamp
* Comment: string
