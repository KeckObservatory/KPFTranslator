# Building Observing Blocks (OBs)

The basic unit of KPF nighttime operations is the Observing Block (OB). An OB describes a single visit to a science target and the observations made there. The data contained in the OB is a set of keyword-value pairs. 

Observers can create OBs in 3 ways:

* As text files which can be read in by the KPF software and executed.
* As a database entry by filling out an OB via the [KPF-CC Web Form](https://www3.keck.hawaii.edu/login/?url=https://www3.keck.hawaii.edu/observers/kpf-cc/rel/index.html?). Please note that the KPF-CC web form is not capable of recording all features of an OB, but should cover 90+% of use cases.  Classical observers are also welcome to use the form.
* Building an OB "live" using the KPF OB GUI.

The data in an OB can be divided in to three categories:

**Target**: The OB will contain information about the target beyond what is in a typical Keck Star List entry in order to flow that information to the FITS header and the data reduction pipeline (DRP).  The target section is only needed if the OB has observations (i.e. it is not purely a calibration OB). Here is a description of all [Target Properties](../TargetProperties).

**Calibrations**: An OB can contain calibrations, these are not typically used by the observer (slewcals are handled separately). Here is a description of all [Calibration Properties](../CalibrationProperties). The Calibrations section of an ON is a list of Calibration entries.

**Observations**: Finally, the OB will contain a list of observations to be made of the target. For typical KPF observers, this will only have one entry, but multiple entries are supported. Each entry describes a set of exposures on the target and contains the information on how those exposures should be executed. Here is a description of all [Observation Properties](../ObservationProperties). The Observations section of an ON is a list of Observation entries.

Note that not all properties are needed in every case. For example, an observation with `ExpMeterMode: 'monitor'` will not need values for `ExpMeterBin` and `ExpMeterThreshold`.


## Example On Sky Science OB

This is an example of what the text file form of an OB might look like. The file is a  `yaml` format which resolves in to a python dict with keys for "Target", "Calibrations" and "Observations" (not all are required).  The "Target" entry is a dict with the various [Target Properties](../TargetProperties).  The "Calibrations" entry (if present) is a **list** of dictionaries, each with the various [Calibration Properties](../CalibrationProperties).  Similarly, the "Observations" entry is a **list** of dictionaries, each with the various [Observation Properties](../ObservationProperties).

The example below has a Target, no Calibrations, and a single Observaton:

```
Target:
  TargetName: HR 4710
  GaiaID: DR3 5859393710380907776
  twoMASSID: J12231377-6737534
  Parallax: 19.730
  RadialVelocity: 33.910
  Gmag: 6.11
  Jmag: 4.97
  Teff: 4750
  RA: 12:23:11.79
  Dec: -67:37:49.47
  Equinox: J2000
  PMRA: -11.258
  PMDEC: 0.256
  Epoch: 2016.00
  DRA: 0.000
  DDEC: 0.000
Observations:
- Object: test1
  nExp: 1
  ExpTime: 60
  TriggerCaHK: True
  TriggerGreen: True
  TriggerRed: True
  BlockSky: False
  ExpMeterMode: control
  AutoExpMeter: True
  ExpMeterBin: 1
  ExpMeterThreshold: 10
  TakeSimulCal: True
  AutoNDFilters: True
```