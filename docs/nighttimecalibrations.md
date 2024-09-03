# Nighttime Calibrations

To monitor the instrumental drift, KPF needs calibrations taken throughout the night.  There are two different calibrations that can be taken and each has advantages and disadvantages.  As we fully characterize the instrument and as the DRP evolves, our recommendations for how best to run nighttime calibrations may change, so check back here for updates.

## Recommended Strategy

The current recommendation is to take a slew cal roughly every hour or so.  There is a "Time Since Cal" readout in the upper right of the OB GUI.  When the time since the last calibration exceeds 1 hour, the readout will turn orange.  At 2 hours, it will turn red.  This is only a recommendation, so the decision of when to take a slew cal is up to the observer.  See also the [Observing Procedures](observingprocedures.md#slew-cals) page.

# What is a Slew Cal?

Slew cals are a particular calibration (a single Etalon calibration exposure) which is intended to be taken during a long telescope slew. The best way to execute this is to click the "Execute OB with Slew Cal" button after loading the next desired OB and asking the OA to begin slewing to the target.  You should let the OA know you are running a slew cal as this will close the FIU hatch and direct Etalon light through the FIU which means that they will no longer see the sky on the guider during the calibration (which takes about 2 minutes).  Directing the calibration light through the FIU means that we will be illuminating the science, sky, and simulcal fibers (all 5 traces) with calibration light.

Because the slew cal happens during the slew to a target, it is optimally performed with a science OB so that the guider can be configured for the science target.  This is another case where executing a science OB before the slew has completed is the most efficient observing strategy.

# What are Simultaneous Calibrations (SimulCals)?

Simultaneous Calibration (simulcal) is when the calibration trace (one of the 5 traces on the main science detectors) is illuminated with calibration light (usually the etalon).  This can be done during science observations, but there are a number of caveats and potential pitfalls.

The main concern when using simulcals is to get the appropriate calibration flux.  Because the science exposure time changes depending on the target, the brightness of the light injected in to the simulcal fiber must be modulated to find an appropriate flux.  This is accomplished with two filter wheels in the calibration bench which have neutral density (ND) filters.

Too little simulcal flux is problematic because it makes the calibration less useful, but too much simulcal flux is worse. Even tiny amounts of scattered light or the far wings of an overly bright simulcal PSF can impact the science traces and bias the RV measurements.  Because of this, we have built an automatic system for choosing the ND filters appropriate for the observation.  This is a complex system because it must account for the color of the star as well as the brightness. 
