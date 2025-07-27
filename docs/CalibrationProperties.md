# Calibration Properties

**CalSource**: `str`
  Name of the calibration source

**Object**: `str`
  Object name for the FITS header

**nExp**: `int`
  Number of Exposures

**ExpTime**: `float`
  [seconds] Exposure Time

**TriggerCaHK**: `bool`
  Trigger the Ca H & K detector for this observation?

**TriggerGreen**: `bool`
  Trigger the Green detector for this observation?

**TriggerRed**: `bool`
  Trigger the Red detector for this observation?

**IntensityMonitor**: `bool`
  Run an Intensity Monitor measurement on this lamp before taking data?

**CalND1**: `str`
  Cal Bench filter 1 position. Throughput = 10^-OD. Values: OD 0.1, OD 1.0, OD 1.3, OD 2.0, OD 3.0, OD 4.0

**CalND2**: `str`
  Cal Bench filter 2 position. Throughput = 10^-OD. Values: OD 0.1, OD 0.3, OD 0.5, OD 0.8, OD 1.0, OD 4.0

**OpenScienceShutter**: `bool`
  Open the Source Select Shutter for the Science fiber?

**OpenSkyShutter**: `bool`
  Open the Source Select Shutter for the Sky fiber?

**TakeSimulCal**: `bool`
  Inject simultaneous calibration light on to the detector during exposure?

**WideFlatPos**: `str`
  If the WideFlat source is chosen, which wheel position to use?

**ExpMeterMode**: `str`
  Exposure meter mode? (monitor, control, off)

**ExpMeterExpTime**: `float`
  [seconds] Exposure Time for the exposure meter

**ExpMeterBin**: `int`
  Which wavelength bin to use for exposure meter termination? (1=498nm, 2=604nm, 3=711nm, 4=817nm)

**ExpMeterThreshold**: `float`
  [e-/nm] Threshold flux at the science detector at which to terminate the exposure

