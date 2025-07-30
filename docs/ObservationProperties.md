# Observation Properties

**Object**: `str`
  This value will go in to the FITS header as the OBJECT keyword value. This is can be used as a notes field for the observer to explain how this set of exposures differs from any following observations of this target. This field can be left blank or set to the target name, it is entirely up to the observer.

**nExp**: `int`
  Number of Exposures to take for this observation.

**ExpTime**: `float`
  [seconds] The exposure time in seconds. Note that if the exposure meter is controlling the exposure duration, this exposure time is the maximum value which will be allowed (the exposure meter may cut the exposure short if the desired flux level is reached).

**TriggerCaHK**: `bool`
  Trigger the Ca H & K detector for this observation?

**TriggerGreen**: `bool`
  Trigger the Green detector for this observation?

**TriggerRed**: `bool`
  Trigger the Red detector for this observation?

**BlockSky**: `bool`
  Block the sky fiber during the observation?

**ExpMeterMode**: `str`
  Exposure meter mode (monitor, control, off). In "monitor" the exposure meter will take exposure during the science exposure and record fluxes. This data will be stored in the resulting FITS file can be used to determine the flux weighted exposure midpoint in time for accurate barycentric correction.  In "control" the exposure meter will terminate the exposure when the desired threshold is reached (see ExpMeterBin and ExpMeterThreshold)

**AutoExpMeter**: `bool`
  Set the exposure time on the exposure meter automatically based on the target G magnitude?

**ExpMeterExpTime**: `float`
  [seconds] The exposure time in seconds for individual exposure meter exposures. This is ignored if AutoExpMeter is True.

**ExpMeterBin**: `int`
  Which wavelength bin to use for exposure meter termination? (1=498nm, 2=604nm, 3=711nm, 4=817nm)

**ExpMeterThreshold**: `float`
  [Mphotons/angstrom] Flux at the science detector at peak of order at which to terminate the exposure

**TakeSimulCal**: `bool`
  Inject simultaneous calibration light on to the detector during exposure?

**AutoNDFilters**: `bool`
  Automatically set ND filters for the simultaneous calibration light? This requires that Teff be within the allowed range of the exposure time calculator software (2700 - 6600 K).

**CalND1**: `str`
  Cal Bench filter 1 position. Throughput = 10^-OD. Values: OD 0.1, OD 1.0, OD 1.3, OD 2.0, OD 3.0, OD 4.0

**CalND2**: `str`
  Cal Bench filter 2 position. Throughput = 10^-OD. Values: OD 0.1, OD 0.3, OD 0.5, OD 0.8, OD 1.0, OD 4.0

**NodN**: `float`
  [arcseconds] Distance to nod the telescope North before starting exposure.

**NodE**: `float`
  [arcseconds] Distance to nod the telescope East before starting exposure.

**GuideHere**: `bool`
  Should the tip tilt system try to lock on to target at this position?

