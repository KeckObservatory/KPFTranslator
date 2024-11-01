# KPF Database Tables

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


## OB Execution History

* OB Unique ID: 
* Timestamp: timestamp
* Exposures: list of floats


## OB Comment History

* OB Unique ID: 
* Timestamp: timestamp
* Comment: string
